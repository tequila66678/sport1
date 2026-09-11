# -*- coding: utf-8 -*-
import json
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_school_admin
from ..database import get_db
from ..models import Admin, Class, School, SportEvent, Student, FaceEmbedding, Score, ScoringStandard
from ..schemas import (DeviceSyncOut, StudentSync, FaceSync, LongRunEvent,
                       DeviceScoreBatch, DeviceScoreResult)
from ..scoring import calculate_score

router = APIRouter(prefix="/api/device", tags=["device"])


def _require_school_id(current: Admin) -> int:
    sid = getattr(current, "current_school_id", None)
    if sid is None:
        raise HTTPException(status_code=400, detail="请先选择学校（或使用学校管理员账号）")
    return sid


@router.get("/sync", response_model=DeviceSyncOut)
def device_sync(db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    sid = _require_school_id(current)
    school = db.query(School).get(sid)
    students = db.query(Student).join(Class, Student.class_id == Class.id) \
        .filter(Class.school_id == sid).all()
    students.sort(key=lambda s: (s.class_.name, s.student_id))
    # 只下发当前模型空间（sface）的特征：旧 faceapi 特征与 sface 不可比，
    # 混下到设备会让 rankMatches 在两种度量下乱认人。旧行保留在库中，重录即覆盖。
    faces = db.query(FaceEmbedding).filter(
        FaceEmbedding.school_id == sid,
        FaceEmbedding.model == "sface",
    ).all()
    face_map = {f.student_id: f for f in faces}
    events = db.query(SportEvent).filter(
        SportEvent.school_id == sid,
        (SportEvent.name.contains("800")) | (SportEvent.name.contains("1000")),
    ).all()
    return DeviceSyncOut(
        school_id=sid,
        school_name=school.name if school else "",
        students=[
            StudentSync(id=s.id, student_id=s.student_id, name=s.name,
                        gender=s.gender.value if s.gender else "",
                        class_name=s.class_.name)
            for s in students
        ],
        face_embeddings=[
            FaceSync(id=st.id, embedding=json.loads(face_map[st.id].embedding))
            for st in students if st.id in face_map
        ],
        long_run_events=[
            LongRunEvent(id=e.id, name=e.name, gender=e.gender.value if e.gender else "")
            for e in events
        ],
    )


def _fmt_time(ms: int) -> str:
    """毫秒 → 'M'SS'，如 178000 → "2'58" """
    total_s = ms // 1000
    m, s = divmod(total_s, 60)
    return f"{m}'{s:02d}"


def _raw_to_ms(raw_value) -> int:
    """把库里的 raw_value 解析成毫秒，用于「同分时比时间」判断。

    兼容设备端 "M'SS"（_fmt_time 输出）与人工端 "M:SS" 及纯秒数。
    解析失败/为空 → 返回超大值：视为无有效历史时间，让新成绩可覆盖。
    """
    if raw_value is None:
        return 10 ** 18
    text = str(raw_value).strip()
    if not text:
        return 10 ** 18
    nums = []
    for part in re.split(r"[':：\s]+", text):
        try:
            nums.append(float(part))
        except ValueError:
            return 10 ** 18
    if not nums or any(n < 0 for n in nums):
        return 10 ** 18
    if len(nums) == 1:
        return int(nums[0] * 1000)                        # 纯秒，如 178 / 178.5
    if len(nums) == 2:
        return int((nums[0] * 60 + nums[1]) * 1000)       # M'SS / M:SS
    return int((nums[0] * 3600 + nums[1] * 60 + nums[2]) * 1000)  # H:MM:SS 兜底


def _is_better_score(new_time_ms: int, new_score, existing, old_time_ms: int) -> bool:
    """新成绩是否值得覆盖旧成绩：无历史/无分数 → 是；分更高 → 是；同分更快 → 是；否则否。"""
    if existing is None or existing.earned_score is None:
        return True
    if new_score > existing.earned_score:
        return True
    if new_score < existing.earned_score:
        return False
    return new_time_ms < old_time_ms


@router.post("/scores", response_model=list[DeviceScoreResult])
def device_scores(data: DeviceScoreBatch, db: Session = Depends(get_db),
                  current: Admin = Depends(get_school_admin)):
    sid = _require_school_id(current)
    test_date = data.test_date or date.today()
    q = db.query(SportEvent).filter(SportEvent.id == data.event_id)
    if sid is not None:
        q = q.filter(SportEvent.school_id == sid)
    event = q.first()
    if not event:
        raise HTTPException(status_code=404, detail="项目不存在")
    standards = db.query(ScoringStandard).filter(ScoringStandard.event_id == event.id).all()
    results: list[DeviceScoreResult] = []
    for entry in data.scores:
        if entry.time_ms <= 0:
            results.append(DeviceScoreResult(ok=False, student_id=entry.student_id, reason="成绩无效"))
            continue
        student = db.query(Student).get(entry.student_id)
        if not student:
            results.append(DeviceScoreResult(ok=False, student_id=entry.student_id, reason="学生不存在"))
            continue
        if student.class_.school_id != sid:
            results.append(DeviceScoreResult(ok=False, student_id=entry.student_id, reason="学生不属于当前学校"))
            continue
        if event.gender.value != "both" and event.gender.value != student.gender.value:
            results.append(DeviceScoreResult(ok=False, student_id=entry.student_id,
                                             reason=f"性别与项目不符（该生为{'女' if student.gender.value=='F' else '男'}）"))
            continue
        raw_value = _fmt_time(entry.time_ms)
        try:
            earned = calculate_score(raw_value, event, standards, student.gender.value)
        except Exception:
            results.append(DeviceScoreResult(ok=False, student_id=entry.student_id,
                                             reason="算分异常（时间格式不匹配）"))
            continue
        existing = db.query(Score).filter(
            Score.student_id == student.id,
            Score.event_id == event.id,
            Score.test_date == test_date,
        ).first()
        if existing is not None and not _is_better_score(entry.time_ms, earned, existing, _raw_to_ms(existing.raw_value)):
            # 库里已有更好成绩（分更高，或同分更快）：保留旧值不覆盖。
            # 响应回填真实入库值，避免前端误以为新成绩已写入。
            results.append(DeviceScoreResult(ok=True, student_id=entry.student_id,
                                             raw_value=existing.raw_value, earned_score=existing.earned_score))
            continue
        if existing:
            existing.raw_value = raw_value
            existing.earned_score = earned
            existing.recorder_id = current.id
        else:
            db.add(Score(student_id=student.id, event_id=event.id, raw_value=raw_value,
                         earned_score=earned, test_date=test_date,
                         recorder_id=current.id, school_id=sid))
        results.append(DeviceScoreResult(ok=True, student_id=entry.student_id,
                                         raw_value=raw_value, earned_score=earned))
    db.commit()
    return results
