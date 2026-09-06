# -*- coding: utf-8 -*-
"""多校同号：学生登录必须按学校定位，未传校且同号歧义时必须拒绝。"""
from app.database import SessionLocal
from app.models import Student, Class, Gender
from app.auth import hash_password


def _add_dup_student(d):
    """在 B 校造一个与 A 校 270101 同号的学生，返回其姓名"""
    db = SessionLocal()
    try:
        cls_b = db.query(Class).filter(Class.school_id == d["other_school_id"]).first()
        db.add(Student(student_id=d["stu_f_sid"], name="赵同号", gender=Gender.F,
                       class_id=cls_b.id, password_hash=hash_password("123456")))
        db.commit()
        return cls_b.id
    finally:
        db.close()


def test_student_login_scoped_by_school(env):
    """同号跨校：带 school_id 各登各校；不带 school_id 歧义 → 401"""
    client, d = env
    _add_dup_student(d)
    school_a = d["school_id"]
    school_b = d["other_school_id"]

    # 带 A 校 → 登进 A 校的李女
    r = client.post("/api/student/login", json={
        "student_id": d["stu_f_sid"], "password": "123456", "school_id": school_a})
    assert r.status_code == 200
    assert r.json()["student"]["name"] == "李女"

    # 带 B 校 → 登进 B 校的同号学生
    r = client.post("/api/student/login", json={
        "student_id": d["stu_f_sid"], "password": "123456", "school_id": school_b})
    assert r.status_code == 200
    assert r.json()["student"]["name"] == "赵同号"

    # 不带学校：跨校同号无法唯一确定 → 401
    r = client.post("/api/student/login", json={
        "student_id": d["stu_f_sid"], "password": "123456"})
    assert r.status_code == 401

    # 学校错了（该学号不在 A 校之外乱指）→ 401
    # 280101 只在 B 校，用 A 校登 → 401
    r = client.post("/api/student/login", json={
        "student_id": "280101", "password": "123456", "school_id": school_a})
    assert r.status_code == 401
