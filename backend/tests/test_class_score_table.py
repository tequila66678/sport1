# -*- coding: utf-8 -*-
"""班级成绩矩阵：行必须带学生内部 id，供前端点行跳「个人追踪」使用。"""
from .conftest import auth_headers


def test_class_score_table_row_has_student_id(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.get("/api/scores/class-score-table", headers=h,
                   params={"class_id": d["cls_f"]})
    assert r.status_code == 200
    body = r.json()
    assert body["students"], "班级应有学生"
    row = body["students"][0]
    # 行既能定位（学号），也能直接跳到内部 id 对应的个人追踪
    assert row["student_id"] == d["stu_f_sid"]
    assert row["id"] == d["stu_f"]
    assert "scores" in row
