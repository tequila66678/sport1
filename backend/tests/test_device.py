# -*- coding: utf-8 -*-
import pytest
from .conftest import auth_headers


def test_sync_requires_login(env):
    client, _ = env
    r = client.get("/api/device/sync")
    assert r.status_code in (401, 403)


def test_sync_returns_school_scope(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.get("/api/device/sync", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["school_id"] == d["school_id"]
    assert len(body["students"]) == 2
    # 给女生录一条人脸，应出现在 face_embeddings。
    # 走 PUT /api/faces 而非直插库：下发的是当前 sface 空间的标，直插的行默认 faceapi 会被过滤。
    client.put(f"/api/faces/{d['stu_f']}", headers=h, json={"embedding": [0.0] * 128})
    r2 = client.get("/api/device/sync", headers=h).json()
    assert any(f["id"] == d["stu_f"] for f in r2["face_embeddings"])
    names = [e["name"] for e in r2["long_run_events"]]
    assert any("800" in n for n in names) and any("1000" in n for n in names)


def _post_scores(client, h, d, event_key, stu, ms):
    return client.post("/api/device/scores", headers=h, json={
        "event_id": d[event_key],
        "test_date": "2026-09-02",
        "scores": [{"student_id": stu, "time_ms": ms}],
    })


def test_device_scores_ok(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = _post_scores(client, h, d, "ev800", d["stu_f"], 178000)
    assert r.status_code == 200
    item = r.json()[0]
    assert item["ok"] is True
    assert item["raw_value"] == "2'58"
    assert item["earned_score"] == 10  # 2'58 <= 3'25 → 满分


def test_device_scores_parity_with_manual(env):
    """设备上传与直接算分路径的 raw/得分一致（对拍）"""
    from app.scoring import calculate_score
    from app.database import SessionLocal
    from app.models import SportEvent, ScoringStandard
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.post("/api/device/scores", headers=h, json={
        "event_id": d["ev800"], "test_date": "2026-09-02",
        "scores": [{"student_id": d["stu_f"], "time_ms": 178000}]})
    device = r.json()[0]
    db = SessionLocal()
    ev = db.query(SportEvent).get(d["ev800"])
    stds = db.query(ScoringStandard).filter(ScoringStandard.event_id == d["ev800"]).all()
    expected = calculate_score("2'58", ev, stds, "F")
    db.close()
    assert device["earned_score"] == expected == 10


def test_device_scores_gender_mismatch(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = _post_scores(client, h, d, "ev1000", d["stu_f"], 178000)  # 女生跑1000米
    item = r.json()[0]
    assert item["ok"] is False
    assert "性别" in item["reason"]


def test_device_scores_unknown_student(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = _post_scores(client, h, d, "ev800", 999999, 178000)
    assert r.json()[0]["ok"] is False
    assert "不存在" in r.json()[0]["reason"]


def test_device_scores_upsert_dedup(env):
    """同学生+同项目+同日重复上传 → 只保留一条记录，且保最好成绩（同分更快才覆盖）"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    _post_scores(client, h, d, "ev800", d["stu_f"], 178000)  # 2'58 满分
    _post_scores(client, h, d, "ev800", d["stu_f"], 183000)  # 3'03 同分更慢 → 不覆盖（保最好）
    _post_scores(client, h, d, "ev800", d["stu_f"], 172000)  # 2'52 同分更快 → 覆盖
    from app.database import SessionLocal
    from app.models import Score
    db = SessionLocal()
    n = db.query(Score).filter(Score.student_id == d["stu_f"],
                               Score.event_id == d["ev800"]).count()
    raw = db.query(Score).filter(Score.student_id == d["stu_f"],
                                 Score.event_id == d["ev800"]).one().raw_value
    db.close()
    assert n == 1
    assert raw == "2'52"  # 最终保留最快成绩


def test_device_scores_cross_school_rejected(env):
    """学校A 管理员向设备上报他校(学校B)学生成绩 → 该条 ok=False 且 reason 含「不属于」"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.post("/api/device/scores", headers=h, json={
        "event_id": d["ev800"], "test_date": "2026-09-02",
        "scores": [{"student_id": d["other_stu"], "time_ms": 178000}]})
    assert r.status_code == 200
    item = r.json()[0]
    assert item["ok"] is False
    assert "不属于" in item["reason"]


def test_device_scores_time_ms_zero_rejected(env):
    """time_ms <= 0 应被 schema 拒绝（422），不能进算分"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.post("/api/device/scores", headers=h, json={
        "event_id": d["ev800"], "test_date": "2026-09-02",
        "scores": [{"student_id": d["stu_f"], "time_ms": 0}]})
    assert r.status_code == 422


def test_device_scores_event_gender_both(env):
    """gender=both 长跑项目：男女学生各自上报都能正常算分 ok=True"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.post("/api/device/scores", headers=h, json={
        "event_id": d["ev800b"], "test_date": "2026-09-02",
        "scores": [
            {"student_id": d["stu_m"], "time_ms": 178000},  # 男 2'58
            {"student_id": d["stu_f"], "time_ms": 183000},  # 女 3'03
        ]})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert all(i["ok"] is True for i in items)
    assert all(i["earned_score"] == 10 for i in items)  # 均优于 3'25 → 满分
