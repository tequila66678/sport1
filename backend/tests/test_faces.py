# -*- coding: utf-8 -*-
from .conftest import auth_headers


def test_put_face_ok(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.put(f"/api/faces/{d['stu_f']}", headers=h, json={"embedding": [0.1] * 128})
    assert r.status_code == 200 and r.json()["ok"] is True


def test_put_face_wrong_length(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.put(f"/api/faces/{d['stu_f']}", headers=h, json={"embedding": [0.1] * 10})
    assert r.status_code == 400


def test_put_face_unknown_student(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.put("/api/faces/999999", headers=h, json={"embedding": [0.1] * 128})
    assert r.status_code == 404


def test_batch_face_mixed(env):
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.post("/api/faces/batch", headers=h, json={"faces": [
        {"student_id": d["stu_f"], "embedding": [0.1] * 128},
        {"student_id": 888888, "embedding": [0.1] * 128},
    ]})
    items = r.json()
    assert items[0]["ok"] is True
    assert items[1]["ok"] is False
