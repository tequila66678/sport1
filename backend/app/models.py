from sqlalchemy import Column, Integer, String, Boolean, Date, Float, DateTime, ForeignKey, Enum as SqlEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    both = "both"

class InputFormat(str, enum.Enum):
    time_ms = "time_ms"
    decimal_seconds = "decimal_seconds"
    decimal_meters = "decimal_meters"
    integer = "integer"

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String, nullable=False)
    name = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School")
    students = relationship("Student", back_populates="class_")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(6), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    password_hash = Column(String, nullable=False)
    class_ = relationship("Class", back_populates="students")
    scores = relationship("Score", back_populates="student")

class SportEvent(Base):
    __tablename__ = "sport_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False)
    higher_better = Column(Boolean, nullable=False)
    unit = Column(String, nullable=False)
    input_format = Column(SqlEnum(InputFormat), nullable=False)
    sort_order = Column(Integer, default=0)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School")
    standards = relationship("ScoringStandard", back_populates="event", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="event")

class ScoringStandard(Base):
    __tablename__ = "scoring_standards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("sport_events.id"), nullable=False)
    gender = Column(SqlEnum(Gender), nullable=False, default="both")
    score = Column(Integer, nullable=False)
    standard_value = Column(String, nullable=False)
    event = relationship("SportEvent", back_populates="standards")

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("sport_events.id"), nullable=False)
    raw_value = Column(String, nullable=False)
    earned_score = Column(Integer, nullable=False)
    test_date = Column(Date, nullable=False)
    recorder_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School")
    student = relationship("Student", back_populates="scores")
    event = relationship("SportEvent", back_populates="scores")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_super = Column(Boolean, default=False)  # deprecated, use role instead
    role = Column(String(20), nullable=False, default='teacher')  # 'super' | 'school_admin' | 'teacher'
    display_name = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    school = relationship("School")

class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    school = relationship("School")
    __table_args__ = (UniqueConstraint("key", "school_id", name="uq_config_key_school"),)

class AttendanceStatus(str, enum.Enum):
    present = "present"    # 出勤
    late = "late"          # 迟到
    excused = "excused"    # 请假
    absent = "absent"      # 缺勤

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    label = Column(String(50), nullable=True)
    recorder_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    school = relationship("School")
    class_ = relationship("Class")
    recorder = relationship("Admin")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(SqlEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.present)
    remark = Column(String(200), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    school = relationship("School")
    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student")
