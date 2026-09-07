from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SystemConfig, Admin, School, Student, SportEvent, Score
from ..schemas import ConfigUpdate, ConfigOut
from ..auth import get_school_admin, require_school

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("", response_model=list[ConfigOut])
def list_config(db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    sid = require_school(current)
    q = db.query(SystemConfig)
    if sid is not None:
        q = q.filter(SystemConfig.school_id == sid)
    return q.all()

@router.get("/public")
def get_public_config(school_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(SystemConfig)
    if school_id:
        q = q.filter(SystemConfig.school_id == school_id)
    configs = q.all()
    result = {}
    for c in configs:
        if c.key in ("school_name", "designer"):
            result[c.key] = c.value
    # if no school_id given, try first school
    if not result.get("school_name"):
        schools = db.execute("SELECT value FROM system_config WHERE key='school_name' LIMIT 1")
        row = schools.fetchone()
        if row:
            result["school_name"] = row[0]
    return result

@router.get("/public/stats")
def get_public_stats(db: Session = Depends(get_db)):
    """欢迎页公开统计：只返回聚合计数，不含任何学生/成绩明细（无隐私风险，无需登录）。
    项目按名称去重计数，避免各校同名项目（如 800米跑）被重复统计。"""
    schools = db.query(School).count()
    students = db.query(Student).count()
    events = db.query(func.count(func.distinct(SportEvent.name))).scalar() or 0
    scores = db.query(Score).count()
    return {"schools": schools, "students": students, "events": events, "scores": scores}

@router.put("/{key}")
def update_config(key: str, data: ConfigUpdate, db: Session = Depends(get_db), current: Admin = Depends(get_school_admin)):
    sid = require_school(current)
    config = db.query(SystemConfig).filter(
        SystemConfig.key == key, SystemConfig.school_id == sid
    ).first()
    if not config:
        config = SystemConfig(key=key, value=data.value, school_id=sid)
        db.add(config)
    else:
        config.value = data.value
    db.commit()
    return {"ok": True, "key": key, "value": data.value}
