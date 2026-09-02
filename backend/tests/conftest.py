# -*- coding: utf-8 -*-
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
sys.path.insert(0, BASE)

# 必须在 import app 之前设置，让 app 的 engine 指向测试库
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(BASE, "tests", "_test.db").replace("\\", "/")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import engine, SessionLocal, Base
from app.models import School, Class, Student, SportEvent, ScoringStandard, Admin, FaceEmbedding, Gender, InputFormat
from app.auth import hash_password, create_jwt


def seed_data(db: Session) -> dict:
    """构造：1 学校 / 2 班 / 男女生各 1 / 800米(F)+1000米(M) 各带标准 / 1 学校管理员。返回关键 id。"""
    school = School(name="测试学校")
    db.add(school); db.flush()
    cls_f = Class(grade="2027届", name="1班", school_id=school.id)
    cls_m = Class(grade="2027届", name="2班", school_id=school.id)
    db.add_all([cls_f, cls_m]); db.flush()

    stu_f = Student(student_id="270101", name="李女", gender=Gender.F, class_id=cls_f.id, password_hash=hash_password("123456"))
    stu_m = Student(student_id="270201", name="王男", gender=Gender.M, class_id=cls_m.id, password_hash=hash_password("123456"))
    db.add_all([stu_f, stu_m]); db.flush()

    ev800 = SportEvent(name="800米跑", gender=Gender.F, higher_better=False, unit="分'秒", input_format=InputFormat.time_ms, sort_order=1, school_id=school.id)
    ev1000 = SportEvent(name="1000米跑", gender=Gender.M, higher_better=False, unit="分'秒", input_format=InputFormat.time_ms, sort_order=1, school_id=school.id)
    db.add_all([ev800, ev1000]); db.flush()
    db.add_all([
        ScoringStandard(event_id=ev800.id, gender=Gender.F, score=10, standard_value="3'25"),
        ScoringStandard(event_id=ev800.id, gender=Gender.F, score=1, standard_value="4'55"),
        ScoringStandard(event_id=ev1000.id, gender=Gender.M, score=10, standard_value="3'40"),
        ScoringStandard(event_id=ev1000.id, gender=Gender.M, score=1, standard_value="5'10"),
    ])

    admin = Admin(username="dev", password_hash=hash_password("pw"), role="school_admin",
                  display_name="测试老师", school_id=school.id)
    db.add(admin); db.flush()
    db.commit()
    return {"school_id": school.id, "cls_f": cls_f.id, "cls_m": cls_m.id,
            "stu_f": stu_f.id, "stu_m": stu_m.id, "stu_f_sid": stu_f.student_id,
            "ev800": ev800.id, "ev1000": ev1000.id, "admin": admin.id}


def auth_headers(admin_db_id: int, school_id: int) -> dict:
    token = create_jwt(admin_db_id, "dev", school_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def env():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        data = seed_data(db)
    finally:
        db.close()
    client = TestClient(app)  # 不进入 context → 不触发 startup seed
    return client, data
