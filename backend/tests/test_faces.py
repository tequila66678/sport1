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


def test_put_face_cross_school_rejected(env):
    """学校A 管理员不能给学校B 学生录脸 → 404"""
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.put(f"/api/faces/{d['other_stu']}", headers=h, json={"embedding": [0.1] * 128})
    assert r.status_code == 404


def test_put_face_marks_sface_model(env):
    """录脸写入的必须是 sface 空间标记；旧 faceapi 特征与 sface 不可比。"""
    import json
    from app.database import SessionLocal
    from app.models import FaceEmbedding
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    r = client.put(f"/api/faces/{d['stu_f']}", headers=h, json={"embedding": [0.1] * 128})
    assert r.status_code == 200
    db = SessionLocal()
    rec = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == d["stu_f"]).first()
    model = rec.model
    db.close()
    assert model == "sface"


def test_sync_skips_faceapi_embeddings(env):
    """设备同步只下发 sface 特征：混入 faceapi 会在设备端乱认人。"""
    import json
    from app.database import SessionLocal
    from app.models import FaceEmbedding
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])

    db = SessionLocal()
    db.add(FaceEmbedding(student_id=d["stu_f"], embedding=json.dumps([0.0] * 128),
                         school_id=d["school_id"], model="faceapi"))
    db.commit(); db.close()
    assert client.get("/api/device/sync", headers=h).json()["face_embeddings"] == []

    # 就地重录 → 覆盖为 sface，此后才下发
    client.put(f"/api/faces/{d['stu_f']}", headers=h, json={"embedding": [0.1] * 128})
    ids = [f["id"] for f in client.get("/api/device/sync", headers=h).json()["face_embeddings"]]
    assert ids == [d["stu_f"]]


def test_delete_student_cascades_face_embedding(env):
    """删除学生应级联删除其 FaceEmbedding（不留孤儿行 / 不触发 FK IntegrityError）"""
    import json
    from app.database import SessionLocal
    from app.models import FaceEmbedding
    client, d = env
    h = auth_headers(d["admin"], d["school_id"])
    db = SessionLocal()
    db.add(FaceEmbedding(student_id=d["stu_f"], embedding=json.dumps([0.0] * 128),
                         school_id=d["school_id"]))
    db.commit(); db.close()
    r = client.delete(f"/api/students/{d['stu_f']}", headers=h)
    assert r.status_code == 200
    db = SessionLocal()
    n = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == d["stu_f"]).count()
    db.close()
    assert n == 0
