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
    # 给女生写一条特征，应出现在 face_embeddings
    from app.database import SessionLocal
    from app.models import FaceEmbedding
    import json
    db = SessionLocal()
    db.add(FaceEmbedding(student_id=d["stu_f"], embedding=json.dumps([0.0] * 128),
                         school_id=d["school_id"]))
    db.commit(); db.close()
    r2 = client.get("/api/device/sync", headers=h).json()
    assert any(f["id"] == d["stu_f"] for f in r2["face_embeddings"])
    names = [e["name"] for e in r2["long_run_events"]]
    assert any("800" in n for n in names) and any("1000" in n for n in names)
