from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_FILE = os.path.join(DATABASE_DIR, "flexi_training.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True)
    batch_name = Column(String(150), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)
    coordinator_name = Column(String(150), nullable=False)
    status = Column(String(30), nullable=False, default="Active")

    trainees = relationship("Trainee", back_populates="batch", cascade="all, delete-orphan")
    faculty_sessions = relationship(
        "FacultySession",
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class Trainee(Base):
    __tablename__ = "trainees"
    __table_args__ = (UniqueConstraint("personal_no", "batch_id", name="uq_trainee_batch"),)
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    ticket_no = Column(String(50), nullable=False)
    personal_no = Column(String(50), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    batch = relationship("Batch", back_populates="trainees")
    attendance = relationship(
        "Attendance",
        back_populates="trainee",
        uselist=False,
        cascade="all, delete-orphan",
    )
    pre_test = relationship(
        "PreTest",
        back_populates="trainee",
        uselist=False,
        cascade="all, delete-orphan",
    )
    post_test = relationship(
        "PostTest",
        back_populates="trainee",
        uselist=False,
        cascade="all, delete-orphan",
    )
    department_allocation = relationship(
        "DepartmentAllocation",
        back_populates="trainee",
        uselist=False,
        cascade="all, delete-orphan",
    )
    audit_trail = relationship(
        "AuditTrail",
        back_populates="trainee",
        cascade="all, delete-orphan",
    )


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False, unique=True)
    attendance_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    day1_status = Column(String(20), nullable=True, default="Absent")
    day2_status = Column(String(20), nullable=True, default="Absent")
    status = Column(String(20), nullable=False, default="Present")
    remarks = Column(Text, nullable=True)

    trainee = relationship("Trainee", back_populates="attendance")


class PreTest(Base):
    __tablename__ = "pretests"
    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False, unique=True)
    score = Column(Integer, nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    remarks = Column(Text, nullable=True)

    trainee = relationship("Trainee", back_populates="pre_test")


class PostTest(Base):
    __tablename__ = "posttests"
    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False, unique=True)
    score = Column(Integer, nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    remarks = Column(Text, nullable=True)

    trainee = relationship("Trainee", back_populates="post_test")


class DepartmentAllocation(Base):
    __tablename__ = "department_allocations"
    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False, unique=True)
    department = Column(String(150), nullable=False)
    allocated_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    remarks = Column(Text, nullable=True)

    trainee = relationship("Trainee", back_populates="department_allocation")


class FacultySession(Base):
    __tablename__ = "faculty_sessions"
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    faculty_name = Column(String(150), nullable=False)
    session_date = Column(Date, nullable=False)
    topic = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)

    batch = relationship("Batch", back_populates="faculty_sessions")


class AuditTrail(Base):
    __tablename__ = "audit_trail"
    id = Column(Integer, primary_key=True)
    trainee_id = Column(Integer, ForeignKey("trainees.id"), nullable=False)
    changed_field = Column(String(150), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    trainee = relationship("Trainee", back_populates="audit_trail")


class UploadHistory(Base):
    __tablename__ = "upload_history"
    id = Column(Integer, primary_key=True)
    module_name = Column(String(150), nullable=False, default="Unknown")
    batch_id = Column(Integer, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_type = Column(String(100), nullable=False)
    uploaded_by = Column(String(150), nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_records = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="Success")
    notes = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    batch_columns = {col["name"] for col in inspector.get_columns("batches")}
    upload_history_columns = {col["name"] for col in inspector.get_columns("upload_history")}
    attendance_columns = {col["name"] for col in inspector.get_columns("attendance")}
    trainee_columns = {col["name"] for col in inspector.get_columns("trainees")}

    # Migrate old unique constraint to composite constraint
    try:
        with engine.begin() as connection:
            # Check if old unique constraint exists
            trainees_constraints = inspector.get_unique_constraints("trainees")
            has_old_constraint = any("uq_trainee_personal_no" in str(c) for c in trainees_constraints)
            
            if has_old_constraint:
                # SQLite doesn't support dropping constraints directly, so we recreate the table
                connection.exec_driver_sql("""
                    CREATE TABLE trainees_new AS 
                    SELECT * FROM trainees
                """)
                connection.exec_driver_sql("DROP TABLE trainees")
                connection.exec_driver_sql("""
                    CREATE TABLE trainees (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        ticket_no VARCHAR(50) NOT NULL,
                        personal_no VARCHAR(50) NOT NULL,
                        batch_id INTEGER NOT NULL,
                        FOREIGN KEY(batch_id) REFERENCES batches(id),
                        UNIQUE(personal_no, batch_id)
                    )
                """)
                connection.exec_driver_sql("""
                    INSERT INTO trainees SELECT * FROM trainees_new
                """)
                connection.exec_driver_sql("DROP TABLE trainees_new")
    except Exception as e:
        print(f"Migration note (old constraint): {e}")

    if "location" not in batch_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE batches ADD COLUMN location VARCHAR(255)")
    if "coordinator_name" not in batch_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE batches ADD COLUMN coordinator_name VARCHAR(150)")

    if "module_name" not in upload_history_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE upload_history ADD COLUMN module_name VARCHAR(150) DEFAULT 'Unknown'")
    if "batch_id" not in upload_history_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE upload_history ADD COLUMN batch_id INTEGER")
    if "total_records" not in upload_history_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE upload_history ADD COLUMN total_records INTEGER DEFAULT 0")

    if "day1_status" not in attendance_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE attendance ADD COLUMN day1_status VARCHAR(20) DEFAULT 'Absent'")
    if "day2_status" not in attendance_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE attendance ADD COLUMN day2_status VARCHAR(20) DEFAULT 'Absent'")

    # Migrate existing records from remarks to day1_status and day2_status
    session = SessionLocal()
    try:
        migration_needed = False
        sample_record = session.query(Attendance).filter(Attendance.remarks.isnot(None)).first()
        if sample_record and sample_record.day1_status in {None, "Absent"} and sample_record.day2_status in {None, "Absent"}:
            migration_needed = True

        if migration_needed:
            records = session.query(Attendance).filter(Attendance.remarks.isnot(None)).all()
            for record in records:
                remarks = record.remarks or ""
                # Extract day1 status
                if "Day1:" in remarks:
                    try:
                        day1_part = remarks.split("Day1:")[1].split(";")[0].strip()
                        record.day1_status = day1_part if day1_part.lower() in {"present", "absent"} else "Absent"
                    except:
                        record.day1_status = "Absent"
                # Extract day2 status
                if "Day2:" in remarks:
                    try:
                        day2_part = remarks.split("Day2:")[1].split(";")[0].strip()
                        record.day2_status = day2_part if day2_part.lower() in {"present", "absent"} else "Absent"
                    except:
                        record.day2_status = "Absent"
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Migration warning: {e}")
    finally:
        session.close()

