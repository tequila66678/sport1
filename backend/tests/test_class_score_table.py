# -*- coding: utf-8 -*-
"""班级成绩矩阵：行必须带学生内部 id，供前端点行跳「个人追踪」使用。
另覆盖取值规则：一个月内取最好，超期回退最近一次。"""
from datetime import date, timedelta

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


def _add_score(student_id, event_id, school_id, raw, earned, days_ago):
    """直接落库并指定 test_date —— 取值规则是按天数分界的，走接口没法造历史日期。"""
    from app.database import SessionLocal
    from app.models import Score
    db = SessionLocal()
    db.add(Score(student_id=student_id, event_id=event_id, raw_value=raw,
                 earned_score=earned, school_id=school_id,
                 test_date=date.today() - timedelta(days=days_ago)))
    db.commit()
    db.close()


def _table_cell(client, h, d, event_key):
    r = client.get("/api/scores/class-score-table", headers=h,
                   params={"class_id": d["cls_f"]})
    assert r.status_code == 200
    row = next(x for x in r.json()["students"] if x["id"] == d["stu_f"])
    return row["scores"].get(str(d[event_key]))


def test_window_picks_best_within_30_days(env):
    """一个月内有成绩时只在这一个月里挑最好的：40 天前那次 10 分不作数。"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "2'58", 10, days_ago=40)
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "3'30", 6, days_ago=5)
    assert _table_cell(client, h, d, "ev800")["earned_score"] == 6


def test_expired_scores_fall_back_to_most_recent(env):
    """成绩全部超期时回退到最近一次，而不是让这个学生从表里消失。"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "2'58", 10, days_ago=100)
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "4'00", 3, days_ago=40)
    cell = _table_cell(client, h, d, "ev800")
    assert cell is not None
    assert cell["earned_score"] == 3   # 最近一次，不是历史上最高的 10


def test_class_stats_shares_the_table_rule(env):
    """统计卡与成绩表同源：都按「一个月内最好，超期回退最近一次」。
    否则表格里的分数会和上面的平均分/总分预测对不上。"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "2'58", 10, days_ago=100)
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "4'00", 3, days_ago=40)
    r = client.get("/api/scores/class-stats", headers=h, params={"class_id": d["cls_f"]})
    assert r.status_code == 200
    avg = next(e["avg_score"] for e in r.json()["event_avgs"] if e["event_id"] == d["ev800"])
    assert avg == 3
    assert _table_cell(client, h, d, "ev800")["earned_score"] == 3


def test_school_stats_keeps_one_year_window(env):
    """全校统计不在本次改动范围内，仍按一年窗口取最好成绩（锁定范围决策）。"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "2'58", 10, days_ago=100)
    _add_score(d["stu_f"], d["ev800"], d["school_id"], "4'00", 3, days_ago=40)
    r = client.get("/api/scores/school-stats", headers=h)
    assert r.status_code == 200
    avg = next(e["avg_score"] for e in r.json()["event_avgs"] if e["event_id"] == d["ev800"])
    assert avg == 10
