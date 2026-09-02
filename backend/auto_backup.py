# -*- coding: utf-8 -*-
"""sport1 生产数据自动备份程序

从 Supabase（生产持久化数据库）导出全部数据到本地。
仅在数据有改动时覆盖本地备份，防止生产数据丢失后本地无副本。

连接串来源（按优先级）:
  1. 环境变量 SPORT1_BACKUP_DATABASE_URL
  2. 本文件同目录下 local_backup_config.json（已加入 .gitignore，密码不提交）

用法:
  python auto_backup.py            # 执行一次备份（有改动才覆盖）
  python auto_backup.py --test     # 只测试连接与数据，不写文件
  python auto_backup.py --force    # 强制备份（忽略改动检测）

备份输出（local_backup/ 目录，已 gitignore）:
  latest.json            最新全量数据（JSON，含全部表）
  latest_sports.db       由最新数据重建的 SQLite，可直接用于部署/恢复
  20260807-153000.json   带时间戳的历史快照（默认保留最近 30 个）
  _state.json            上次备份内容哈希（用于改动检测）
  _backup.log            运行日志
"""
import json, os, sys, hashlib, sqlite3, glob
from datetime import datetime, date

# ============================ 配置 ============================
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_backup")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_backup_config.json")
KEEP_N = 30                 # 保留最近 N 个带时间戳快照
# ==============================================================

STATE_FILE = os.path.join(BACKUP_DIR, "_state.json")
LOG_FILE = os.path.join(BACKUP_DIR, "_backup.log")
SQLITE_FILE = os.path.join(BACKUP_DIR, "latest_sports.db")
JSON_FILE = os.path.join(BACKUP_DIR, "latest.json")

# 核心业务表（按依赖顺序）
ORDER = ["schools", "classes", "students", "sport_events", "scoring_standards",
         "admins", "system_config", "scores", "attendance_sessions", "attendance_records", "face_embeddings"]

# 与 models.py 严格一致的建表语句（用于重建可部署的 SQLite）
CREATE = {
    "schools": "CREATE TABLE schools (id INTEGER NOT NULL PRIMARY KEY, name VARCHAR NOT NULL)",
    "classes": "CREATE TABLE classes (id INTEGER NOT NULL PRIMARY KEY, grade VARCHAR NOT NULL, name VARCHAR NOT NULL, school_id INTEGER NOT NULL, FOREIGN KEY(school_id) REFERENCES schools(id))",
    "students": "CREATE TABLE students (id INTEGER NOT NULL PRIMARY KEY, student_id VARCHAR(6) NOT NULL UNIQUE, name VARCHAR NOT NULL, gender VARCHAR NOT NULL, class_id INTEGER NOT NULL, password_hash VARCHAR NOT NULL, FOREIGN KEY(class_id) REFERENCES classes(id))",
    "sport_events": "CREATE TABLE sport_events (id INTEGER NOT NULL PRIMARY KEY, name VARCHAR NOT NULL, gender VARCHAR NOT NULL, higher_better BOOLEAN NOT NULL, unit VARCHAR NOT NULL, input_format VARCHAR NOT NULL, sort_order INTEGER, school_id INTEGER NOT NULL, FOREIGN KEY(school_id) REFERENCES schools(id))",
    "scoring_standards": "CREATE TABLE scoring_standards (id INTEGER NOT NULL PRIMARY KEY, event_id INTEGER NOT NULL, gender VARCHAR NOT NULL, score INTEGER NOT NULL, standard_value VARCHAR NOT NULL, FOREIGN KEY(event_id) REFERENCES sport_events(id))",
    "scores": "CREATE TABLE scores (id INTEGER NOT NULL PRIMARY KEY, student_id INTEGER NOT NULL, event_id INTEGER NOT NULL, raw_value VARCHAR NOT NULL, earned_score INTEGER NOT NULL, test_date DATE NOT NULL, recorder_id INTEGER, school_id INTEGER NOT NULL, FOREIGN KEY(student_id) REFERENCES students(id), FOREIGN KEY(event_id) REFERENCES sport_events(id), FOREIGN KEY(recorder_id) REFERENCES admins(id), FOREIGN KEY(school_id) REFERENCES schools(id))",
    "admins": "CREATE TABLE admins (id INTEGER NOT NULL PRIMARY KEY, username VARCHAR NOT NULL UNIQUE, password_hash VARCHAR NOT NULL, is_super BOOLEAN, role VARCHAR(20) NOT NULL, display_name VARCHAR NOT NULL, school_id INTEGER, FOREIGN KEY(school_id) REFERENCES schools(id))",
    "system_config": "CREATE TABLE system_config (id INTEGER NOT NULL PRIMARY KEY, key VARCHAR NOT NULL, value VARCHAR NOT NULL, school_id INTEGER NOT NULL, FOREIGN KEY(school_id) REFERENCES schools(id))",
    "attendance_sessions": "CREATE TABLE attendance_sessions (id INTEGER NOT NULL PRIMARY KEY, class_id INTEGER NOT NULL, session_date DATE NOT NULL, label VARCHAR(50), recorder_id INTEGER, school_id INTEGER NOT NULL, created_at DATETIME, FOREIGN KEY(class_id) REFERENCES classes(id), FOREIGN KEY(school_id) REFERENCES schools(id))",
    "attendance_records": "CREATE TABLE attendance_records (id INTEGER NOT NULL PRIMARY KEY, session_id INTEGER NOT NULL, student_id INTEGER NOT NULL, status VARCHAR NOT NULL, remark VARCHAR(200), school_id INTEGER NOT NULL, FOREIGN KEY(session_id) REFERENCES attendance_sessions(id), FOREIGN KEY(student_id) REFERENCES students(id), FOREIGN KEY(school_id) REFERENCES schools(id))",
    "face_embeddings": "CREATE TABLE face_embeddings (id INTEGER NOT NULL PRIMARY KEY, student_id INTEGER NOT NULL UNIQUE, embedding TEXT NOT NULL, school_id INTEGER NOT NULL, created_at DATETIME, FOREIGN KEY(student_id) REFERENCES students(id), FOREIGN KEY(school_id) REFERENCES schools(id))",
}


def get_database_url():
    """读取数据库连接串：环境变量优先，其次配置文件"""
    url = os.environ.get("SPORT1_BACKUP_DATABASE_URL")
    if url:
        return url
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
            url = cfg.get("database_url") or cfg.get("DATABASE_URL")
            if url:
                return url
        except Exception as e:
            log(f"!! 读取配置文件失败: {e}")
    sys.exit("!! 未找到数据库连接串。请设置环境变量 SPORT1_BACKUP_DATABASE_URL "
             f"或创建 {CONFIG_FILE}（字段 database_url）")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def export_from_supabase(url):
    """连接 Supabase，导出全部核心表。返回 {table: {columns, rows}}"""
    import psycopg2

    conn = psycopg2.connect(url, connect_timeout=20)
    try:
        cur = conn.cursor()
        data = {}
        for t in ORDER:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name=%s ORDER BY ordinal_position", (t,))
            cols = [r[0] for r in cur.fetchall()]
            cur.execute(f'SELECT * FROM "{t}" ORDER BY 1')
            rows = cur.fetchall()
            recs = []
            for r in rows:
                rec = {}
                for c, v in zip(cols, r):
                    if isinstance(v, (datetime, date)):
                        v = v.isoformat()
                    rec[c] = v
                recs.append(rec)
            data[t] = {"columns": cols, "rows": recs}
        return data
    finally:
        conn.close()


def content_hash(data):
    """对全量数据做确定性哈希（内容一致则哈希一致）"""
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def rebuild_sqlite(data, out_path):
    """从导出数据重建可部署的 SQLite（保留原 ID，短学号补零到 6 位）"""
    if os.path.exists(out_path):
        os.remove(out_path)
    conn = sqlite3.connect(out_path)
    cur = conn.cursor()
    for name in ORDER:
        cur.execute(CREATE[name])
    for name in ORDER:
        t = data.get(name)
        if not t or not t.get("columns"):
            continue
        cols, rows = t["columns"], t["rows"]
        placeholders = ",".join("?" for _ in cols)
        col_str = ",".join(cols)
        for r in rows:
            vals = [r.get(c) for c in cols]
            if name == "students":
                idx = cols.index("student_id")
                sid = str(vals[idx])
                if len(sid) < 6:
                    vals[idx] = sid.zfill(6)
            cur.execute(f'INSERT INTO "{name}" ({col_str}) VALUES ({placeholders})', vals)
    conn.commit()
    conn.close()


def prune():
    """删除多余的历史快照，只保留最近 KEEP_N 个"""
    snaps = sorted(glob.glob(os.path.join(BACKUP_DIR, "20*.json")))
    for f in snaps[:-KEEP_N]:
        try:
            os.remove(f)
        except OSError:
            pass


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)


def main():
    test_only = "--test" in sys.argv
    force = "--force" in sys.argv
    os.makedirs(BACKUP_DIR, exist_ok=True)
    url = get_database_url()

    if test_only:
        log("测试模式：仅验证连接与数据")
        data = export_from_supabase(url)
        total = sum(len(t["rows"]) for t in data.values())
        print("  表数:", len(data), "| 总行数:", total)
        for t in ORDER:
            print(f"    {t}: {len(data.get(t, {}).get('rows', []))}")
        log(f"测试完成，共 {total} 行（未写文件）")
        return

    log("开始备份 ...")
    data = export_from_supabase(url)
    total = sum(len(t["rows"]) for t in data.values())
    # 防呆：空导出视为异常，绝不覆盖本地
    if total == 0:
        log("!! 导出为空（可能连接异常），已中止，未覆盖本地备份")
        sys.exit(1)

    new_hash = content_hash(data)
    state = load_state()
    if state.get("hash") == new_hash and not force:
        log(f"数据无改动（hash 一致，{total} 行），跳过覆盖")
        return

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    snap = os.path.join(BACKUP_DIR, f"{ts}.json")
    with open(snap, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)
    rebuild_sqlite(data, SQLITE_FILE)
    state["hash"] = new_hash
    state["last_backup"] = ts
    state["total_rows"] = total
    save_state(state)
    prune()
    log(f"备份完成：{ts}，共 {total} 行 → {BACKUP_DIR}")


if __name__ == "__main__":
    main()
