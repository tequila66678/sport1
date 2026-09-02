# -*- coding: utf-8 -*-
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..models import Admin, Class, School, SportEvent, Student, FaceEmbedding
from ..schemas import (DeviceSyncOut, StudentSync, FaceSync, LongRunEvent)

router = APIRouter(prefix="/api/device", tags=["device"])


def _require_school_id(current: Admin) -> int:
    sid = getattr(current, "current_school_id", None)
    if sid is None:
        raise HTTPException(status_code=400, detail="请先选择学校（或使用学校管理员账号）")
    return sid


@router.get("/sync", response_model=DeviceSyncOut)
def device_sync(db: Session = Depends(get_db), current: Admin = Depends(get_current_admin)):
    sid = _require_school_id(current)
    school = db.query(School).get(sid)
    students = db.query(Student).join(Class, Student.class_id == Class.id) \
        .filter(Class.school_id == sid).all()
    students.sort(key=lambda s: (s.class_.name, s.student_id))
    faces = db.query(FaceEmbedding).filter(FaceEmbedding.school_id == sid).all()
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
