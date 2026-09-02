# -*- coding: utf-8 -*-
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_school_admin
from ..database import get_db
from ..models import Admin, Class, Student, FaceEmbedding
from ..schemas import FaceEmbeddingOnly, FaceBatchWrite, FaceResult

router = APIRouter(prefix="/api/faces", tags=["faces"])


def _find_student(db: Session, sid: int, student_id: int):
    q = db.query(Student).join(Class, Student.class_id == Class.id).filter(Student.id == student_id)
    if sid is not None:
        q = q.filter(Class.school_id == sid)
    return q.first()


def _upsert(db: Session, st: Student, embedding: list[float]):
    rec = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == st.id).first()
    payload = json.dumps(embedding)
    if rec:
        rec.embedding = payload
    else:
        db.add(FaceEmbedding(student_id=st.id, embedding=payload, school_id=st.class_.school_id))


def _require_school_id(current: Admin) -> int:
    sid = getattr(current, "current_school_id", None)
    if sid is None:
        raise HTTPException(status_code=400, detail="请先选择学校（或使用学校管理员账号）")
    return sid


@router.put("/{student_id}")
def put_face(student_id: int, data: FaceEmbeddingOnly, db: Session = Depends(get_db),
             current: Admin = Depends(get_school_admin)):
    sid = _require_school_id(current)
    st = _find_student(db, sid, student_id)
    if not st:
        raise HTTPException(status_code=404, detail="学生不存在或不属于当前学校")
    if len(data.embedding) != 128:
        raise HTTPException(status_code=400, detail="特征长度必须为 128")
    _upsert(db, st, data.embedding)
    db.commit()
    return {"ok": True}


@router.post("/batch", response_model=list[FaceResult])
def batch_faces(data: FaceBatchWrite, db: Session = Depends(get_db),
                current: Admin = Depends(get_school_admin)):
    sid = _require_school_id(current)
    results: list[FaceResult] = []
    for f in data.faces:
        st = _find_student(db, sid, f.student_id)
        if not st:
            results.append(FaceResult(ok=False, student_id=f.student_id, reason="学生不存在或不属于当前学校"))
            continue
        if len(f.embedding) != 128:
            results.append(FaceResult(ok=False, student_id=f.student_id, reason="特征长度必须为 128"))
            continue
        _upsert(db, st, f.embedding)
        results.append(FaceResult(ok=True, student_id=f.student_id))
    db.commit()
    return results
