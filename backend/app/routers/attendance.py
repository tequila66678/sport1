from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..auth import get_current_admin, require_school
from ..models import (
    Admin, Student, Class, AttendanceSession, AttendanceRecord, AttendanceStatus
)
from ..schemas import (
    AttendanceSessionCreate, AttendanceSessionUpdate,
    AttendanceSessionOut, AttendanceRecordOut,
    ClassAttendanceStats, StudentAttendanceStats
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _session_to_out(session: AttendanceSession) -> dict:
    """Convert an AttendanceSession ORM object to a dict matching AttendanceSessionOut."""
    records_out = []
    present = late = excused = absent = 0
    for r in session.records:
        records_out.append(AttendanceRecordOut(
            id=r.id,
            student_id=r.student_id,
            student_name=r.student.name if r.student else "",
            student_gender=r.student.gender if r.student else "",
            status=r.status.value if isinstance(r.status, AttendanceStatus) else r.status,
            remark=r.remark,
        ).model_dump())
        s = r.status.value if isinstance(r.status, AttendanceStatus) else r.status
        if s == "present":
            present += 1
        elif s == "late":
            late += 1
        elif s == "excused":
            excused += 1
        elif s == "absent":
            absent += 1

    return AttendanceSessionOut(
        id=session.id,
        class_id=session.class_id,
        class_name=session.class_.name if session.class_ else "",
        session_date=session.session_date,
        label=session.label,
        recorder_name=session.recorder.display_name if session.recorder else "",
        created_at=session.created_at,
        records=records_out,
        present_count=present,
        late_count=late,
        excused_count=excused,
        absent_count=absent,
    ).model_dump()


@router.post("/sessions")
def create_session(
    data: AttendanceSessionCreate,
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Create an attendance session with all student records."""
    # Verify class exists and belongs to the school
    cls = db.query(Class).filter(Class.id == data.class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    if school_id is not None and cls.school_id != school_id:
        raise HTTPException(403, "无权操作其他学校的数据")

    # Check for existing session on the same class+date
    existing = db.query(AttendanceSession).filter(
        AttendanceSession.class_id == data.class_id,
        AttendanceSession.session_date == data.session_date,
    ).first()
    if existing:
        raise HTTPException(409, f"该班级在 {data.session_date} 已有考勤记录（ID={existing.id}），请使用更新接口")

    # Get all students in the class for validation
    class_student_ids = set(
        s[0] for s in db.query(Student.id).filter(Student.class_id == data.class_id).all()
    )

    session = AttendanceSession(
        class_id=data.class_id,
        session_date=data.session_date,
        label=data.label,
        recorder_id=current.id,
        school_id=cls.school_id,
    )
    db.add(session)
    db.flush()  # get session.id

    for entry in data.records:
        if entry.student_id not in class_student_ids:
            continue  # skip students not in this class
        record = AttendanceRecord(
            session_id=session.id,
            student_id=entry.student_id,
            status=AttendanceStatus(entry.status),
            remark=entry.remark,
            school_id=cls.school_id,
        )
        db.add(record)

    db.commit()
    db.refresh(session)
    return _session_to_out(session)


@router.get("/sessions")
def list_sessions(
    class_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """List attendance sessions with optional filters."""
    q = db.query(AttendanceSession)

    if school_id is not None:
        q = q.filter(AttendanceSession.school_id == school_id)
    if class_id is not None:
        q = q.filter(AttendanceSession.class_id == class_id)
    if date_from:
        q = q.filter(AttendanceSession.session_date >= date_from)
    if date_to:
        q = q.filter(AttendanceSession.session_date <= date_to)

    total = q.count()
    sessions = q.order_by(AttendanceSession.session_date.desc(), AttendanceSession.id.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_session_to_out(s) for s in sessions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/sessions/{session_id}")
def get_session(
    session_id: int,
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get a single attendance session with all records."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "考勤记录不存在")
    if school_id is not None and session.school_id != school_id:
        raise HTTPException(403, "无权查看其他学校的数据")
    return _session_to_out(session)


@router.put("/sessions/{session_id}")
def update_session(
    session_id: int,
    data: AttendanceSessionUpdate,
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Update an attendance session: change label and/or student statuses."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "考勤记录不存在")
    if school_id is not None and session.school_id != school_id:
        raise HTTPException(403, "无权修改其他学校的数据")

    if data.label is not None:
        session.label = data.label

    # Update records: replace existing records for the given students
    if data.records:
        existing_map = {r.student_id: r for r in session.records}
        class_student_ids = set(
            s[0] for s in db.query(Student.id).filter(Student.class_id == session.class_id).all()
        )
        for entry in data.records:
            if entry.student_id not in class_student_ids:
                continue
            if entry.student_id in existing_map:
                rec = existing_map[entry.student_id]
                rec.status = AttendanceStatus(entry.status)
                rec.remark = entry.remark
            else:
                rec = AttendanceRecord(
                    session_id=session.id,
                    student_id=entry.student_id,
                    status=AttendanceStatus(entry.status),
                    remark=entry.remark,
                    school_id=session.school_id,
                )
                db.add(rec)

    db.commit()
    db.refresh(session)
    return _session_to_out(session)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Delete an attendance session (cascade deletes its records)."""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "考勤记录不存在")
    if school_id is not None and session.school_id != school_id:
        raise HTTPException(403, "无权删除其他学校的数据")
    db.delete(session)
    db.commit()
    return {"ok": True}


@router.get("/student-stats/{student_id}")
def student_stats(
    student_id: int,
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get attendance statistics for a single student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, "学生不存在")
    if school_id is not None and student.class_.school_id != school_id:
        raise HTTPException(403, "无权查看其他学校的数据")

    records = db.query(AttendanceRecord).join(AttendanceSession).filter(
        AttendanceRecord.student_id == student_id,
    )
    if school_id is not None:
        records = records.filter(AttendanceSession.school_id == school_id)
    records = records.order_by(AttendanceSession.session_date.desc()).all()

    present = late = excused = absent = 0
    record_dicts = []
    for r in records:
        s = r.status.value if isinstance(r.status, AttendanceStatus) else r.status
        if s == "present":
            present += 1
        elif s == "late":
            late += 1
        elif s == "excused":
            excused += 1
        elif s == "absent":
            absent += 1
        record_dicts.append({
            "session_id": r.session_id,
            "session_date": r.session.session_date,
            "label": r.session.label,
            "status": s,
            "remark": r.remark,
        })

    total = len(records)
    rate = round((present + late) / total * 100, 1) if total > 0 else 100.0

    return StudentAttendanceStats(
        student_id=student.id,
        student_name=student.name,
        class_name=student.class_.name if student.class_ else "",
        total_sessions=total,
        present_count=present,
        late_count=late,
        excused_count=excused,
        absent_count=absent,
        attendance_rate=rate,
        records=record_dicts,
    ).model_dump()


@router.get("/class-stats")
def class_stats(
    class_id: int = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    threshold: float = Query(80.0, ge=0, le=100, description="出勤率预警阈值，低于此值的学生进入预警名单"),
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get attendance statistics for a class, including per-student rates and warnings."""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(404, "班级不存在")
    if school_id is not None and cls.school_id != school_id:
        raise HTTPException(403, "无权查看其他学校的数据")

    # Get all sessions for this class
    sessions_q = db.query(AttendanceSession).filter(AttendanceSession.class_id == class_id)
    if date_from:
        sessions_q = sessions_q.filter(AttendanceSession.session_date >= date_from)
    if date_to:
        sessions_q = sessions_q.filter(AttendanceSession.session_date <= date_to)
    sessions = sessions_q.all()
    session_ids = [s.id for s in sessions]
    total_sessions = len(sessions)

    # Get all students in class
    students = db.query(Student).filter(Student.class_id == class_id).all()

    student_stats = []
    warning_students = []
    all_rates = []

    for student in students:
        if session_ids:
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.session_id.in_(session_ids),
            ).all()
        else:
            records = []

        present = late = excused = absent = 0
        for r in records:
            s = r.status.value if isinstance(r.status, AttendanceStatus) else r.status
            if s == "present":
                present += 1
            elif s == "late":
                late += 1
            elif s == "excused":
                excused += 1
            elif s == "absent":
                absent += 1

        # total for this student = sessions they have records for
        rate = round((present + late) / total_sessions * 100, 1) if total_sessions > 0 else 100.0
        all_rates.append(rate)

        stat = StudentAttendanceStats(
            student_id=student.id,
            student_name=student.name,
            class_name=cls.name,
            total_sessions=total_sessions,
            present_count=present,
            late_count=late,
            excused_count=excused,
            absent_count=absent,
            attendance_rate=rate,
            records=[],
        ).model_dump()
        student_stats.append(stat)

        if total_sessions > 0 and rate < threshold:
            warning_students.append({
                "student_id": student.id,
                "student_name": student.name,
                "attendance_rate": rate,
                "absent_count": absent,
                "total_sessions": total_sessions,
            })

    avg_rate = round(sum(all_rates) / len(all_rates), 1) if all_rates else 0.0

    return ClassAttendanceStats(
        class_id=cls.id,
        class_name=cls.name,
        total_sessions=total_sessions,
        avg_attendance_rate=avg_rate,
        student_stats=student_stats,
        warning_students=warning_students,
    ).model_dump()


@router.get("/warnings")
def warnings(
    threshold: float = Query(80.0, ge=0, le=100, description="出勤率预警阈值"),
    class_id: Optional[int] = Query(None),
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get all students with attendance rate below the threshold across the school."""
    classes_q = db.query(Class)
    if school_id is not None:
        classes_q = classes_q.filter(Class.school_id == school_id)
    if class_id is not None:
        classes_q = classes_q.filter(Class.id == class_id)

    classes = classes_q.all()
    all_warnings = []

    for cls in classes:
        sessions = db.query(AttendanceSession).filter(
            AttendanceSession.class_id == cls.id,
        ).all()
        session_ids = [s.id for s in sessions]
        total_sessions = len(sessions)

        if total_sessions == 0:
            continue

        students = db.query(Student).filter(Student.class_id == cls.id).all()
        for student in students:
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.session_id.in_(session_ids),
            ).all()

            present = late = absent = 0
            for r in records:
                s = r.status.value if isinstance(r.status, AttendanceStatus) else r.status
                if s == "present":
                    present += 1
                elif s == "late":
                    late += 1
                elif s == "absent":
                    absent += 1

            rate = round((present + late) / total_sessions * 100, 1)
            if rate < threshold:
                all_warnings.append({
                    "student_id": student.id,
                    "student_name": student.name,
                    "class_id": cls.id,
                    "class_name": cls.name,
                    "attendance_rate": rate,
                    "absent_count": absent,
                    "total_sessions": total_sessions,
                })

    all_warnings.sort(key=lambda w: w["attendance_rate"])
    return {"warnings": all_warnings, "threshold": threshold, "total": len(all_warnings)}


@router.get("/details")
def attendance_details(
    class_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current: Admin = Depends(get_current_admin),
    school_id: Optional[int] = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get a flat list of abnormal attendance records (late, excused, absent) with session info."""
    q = db.query(AttendanceRecord).join(AttendanceSession).join(Student).join(Class)

    if school_id is not None:
        q = q.filter(AttendanceRecord.school_id == school_id)
    if class_id is not None:
        q = q.filter(AttendanceSession.class_id == class_id)
    if date_from:
        q = q.filter(AttendanceSession.session_date >= date_from)
    if date_to:
        q = q.filter(AttendanceSession.session_date <= date_to)

    # Only abnormal records
    q = q.filter(AttendanceRecord.status.in_([
        AttendanceStatus.late, AttendanceStatus.excused, AttendanceStatus.absent
    ]))

    total = q.count()
    records = q.order_by(
        AttendanceSession.session_date.desc(),
        AttendanceSession.id.desc(),
        Student.id.asc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in records:
        st = r.status.value if isinstance(r.status, AttendanceStatus) else r.status
        status_label = {"late": "迟到", "excused": "请假", "absent": "缺勤"}.get(st, st)
        items.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.name if r.student else "",
            "class_name": r.session.class_.name if r.session.class_ else "",
            "session_id": r.session_id,
            "session_date": str(r.session.session_date),
            "session_label": r.session.label,
            "status": st,
            "status_label": status_label,
            "remark": r.remark,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}
