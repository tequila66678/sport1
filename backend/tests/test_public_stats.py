# -*- coding: utf-8 -*-
"""欢迎页公开统计接口：无需登录，只返回聚合计数（不含个人数据）。"""


def test_public_stats_counts(env):
    """环境构造：2 学校 / 学生 3 人（校A 2 + 校B 1）/ 项目名去重 3 个 / 初始 0 条成绩"""
    client, d = env
    r = client.get("/api/config/public/stats")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"schools", "students", "events", "scores"}
    assert body["schools"] == 2
    assert body["students"] == 3
    # 800米跑 / 1000米跑 / 800米跑（男女通用）——按名称去重，不因各校同名项目重复计数
    assert body["events"] == 3
    assert body["scores"] == 0


def test_public_stats_does_not_require_auth(env):
    client, _ = env
    assert client.get("/api/config/public/stats").status_code == 200


def test_public_stats_no_sensitive_fields(env):
    """只允许出现聚合计数，禁止把学生姓名/学号等细节带出"""
    client, _ = env
    body = client.get("/api/config/public/stats").json()
    assert body.keys() <= {"schools", "students", "events", "scores"}
    assert all(isinstance(v, int) for v in body.values())
