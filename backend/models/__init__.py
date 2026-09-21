from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, inspect
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
    personal_no = Column(String(50), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    # Additional trainee fields imported from the Excel trainee sheet
    gender = Column(String(30), nullable=True)
    grade = Column(String(50), nullable=True)
    day1 = Column(String(20), nullable=True)
    day2 = Column(String(20), nullable=True)
    day3 = Column(String(20), nullable=True)
    day5 = Column(String(20), nullable=True)
    day6 = Column(String(20), nullable=True)
    bolt_tightening = Column(Float, nullable=True)
    nut_tightening = Column(Float, nullable=True)
    screw_tightening = Column(Float, nullable=True)
    screw_grommet = Column(Float, nullable=True)
    plug_hole_grommet = Column(Float, nullable=True)
    connector_connection = Column(Float, nullable=True)
    hose_fitment = Column(Float, nullable=True)
    flare_nut_tight = Column(Float, nullable=True)
    theory = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    re_test = Column(String(50), nullable=True)
    exam_grade = Column(String(50), nullable=True)
    trainer_name = Column(String(255), nullable=True)
    sub_area = Column(String(150), nullable=True)

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
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    session_date = Column(Date, nullable=True)
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

    # Trainee schema migration
    # -------------------------
    # Older databases contain a required `ticket_no` column. The current
    # application no longer uses Ticket No at all, so simply removing the
    # field from the SQLAlchemy model is not enough: SQLite would still reject
    # INSERTs because the old NOT NULL column remains in the physical table.
    #
    # Recreate the trainees table when the legacy column is present. This also
    # preserves existing trainee IDs and data while creating the current
    # composite uniqueness rule (personal_no + batch_id).
    trainee_columns_current = {
        "id": "INTEGER PRIMARY KEY",
        "name": "VARCHAR(150) NOT NULL",
        "personal_no": "VARCHAR(50) NOT NULL",
        "batch_id": "INTEGER NOT NULL",
        "gender": "VARCHAR(30)",
        "grade": "VARCHAR(50)",
        "day1": "VARCHAR(20)",
        "day2": "VARCHAR(20)",
        "day3": "VARCHAR(20)",
        "day5": "VARCHAR(20)",
        "day6": "VARCHAR(20)",
        "bolt_tightening": "FLOAT",
        "nut_tightening": "FLOAT",
        "screw_tightening": "FLOAT",
        "screw_grommet": "FLOAT",
        "plug_hole_grommet": "FLOAT",
        "connector_connection": "FLOAT",
        "hose_fitment": "FLOAT",
        "flare_nut_tight": "FLOAT",
        "theory": "FLOAT",
        "total": "FLOAT",
        "re_test": "VARCHAR(50)",
        "exam_grade": "VARCHAR(50)",
        "trainer_name": "VARCHAR(255)",
        "sub_area": "VARCHAR(150)",
    }

    def recreate_trainees_table(connection):
        # The table may have columns from an intermediate migration, so copy
        # every current column that exists and use NULL for newly introduced
        # fields that are absent in an older database.
        select_parts = []
        insert_columns = []

        for column_name in trainee_columns_current:
            insert_columns.append(column_name)
            if column_name in trainee_columns:
                select_parts.append(f'"{column_name}"')
            else:
                select_parts.append(f"NULL AS \"{column_name}\"")

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("DROP TABLE IF EXISTS trainees_new")

        create_columns = [
            f'"{name}" {definition}'
            for name, definition in trainee_columns_current.items()
            if name != "id"
        ]
        create_sql = """
            CREATE TABLE trainees_new (
                "id" INTEGER PRIMARY KEY,
                "name" VARCHAR(150) NOT NULL,
                "personal_no" VARCHAR(50) NOT NULL,
                "batch_id" INTEGER NOT NULL,
                "gender" VARCHAR(30),
                "grade" VARCHAR(50),
                "day1" VARCHAR(20),
                "day2" VARCHAR(20),
                "day3" VARCHAR(20),
                "day5" VARCHAR(20),
                "day6" VARCHAR(20),
                "bolt_tightening" FLOAT,
                "nut_tightening" FLOAT,
                "screw_tightening" FLOAT,
                "screw_grommet" FLOAT,
                "plug_hole_grommet" FLOAT,
                "connector_connection" FLOAT,
                "hose_fitment" FLOAT,
                "flare_nut_tight" FLOAT,
                "theory" FLOAT,
                "total" FLOAT,
                "re_test" VARCHAR(50),
                "exam_grade" VARCHAR(50),
                "trainer_name" VARCHAR(255),
                "sub_area" VARCHAR(150),
                FOREIGN KEY(batch_id) REFERENCES batches(id),
                UNIQUE(personal_no, batch_id)
            )
        """
        connection.exec_driver_sql(create_sql)

        # Only copy rows if the old table exists. Base.metadata.create_all()
        # may already have created it on a brand-new database.
        if "trainees" in inspect(connection).get_table_names():
            connection.exec_driver_sql(
                f"""
                INSERT INTO trainees_new ({", ".join(f'"{c}"' for c in insert_columns)})
                SELECT {", ".join(select_parts)}
                FROM trainees
                """
            )
            connection.exec_driver_sql("DROP TABLE trainees")

        connection.exec_driver_sql("ALTER TABLE trainees_new RENAME TO trainees")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")

    # Recreate the physical table if Ticket No is still present. This removes
    # both the column and its NOT NULL constraint permanently.
    if "ticket_no" in trainee_columns:
        try:
            with engine.begin() as connection:
                recreate_trainees_table(connection)
            inspector = inspect(engine)
            trainee_columns = {col["name"] for col in inspector.get_columns("trainees")}
        except Exception as e:
            print(f"Migration error (remove ticket_no): {e}")
            raise

    # Add any Excel trainee fields that are missing from an older database.
    # This is also safe for databases that already had Ticket No removed.
    trainee_extra_columns = {
        "gender": "VARCHAR(30)",
        "grade": "VARCHAR(50)",
        "day1": "VARCHAR(20)",
        "day2": "VARCHAR(20)",
        "day3": "VARCHAR(20)",
        "day5": "VARCHAR(20)",
        "day6": "VARCHAR(20)",
        "bolt_tightening": "FLOAT",
        "nut_tightening": "FLOAT",
        "screw_tightening": "FLOAT",
        "screw_grommet": "FLOAT",
        "plug_hole_grommet": "FLOAT",
        "connector_connection": "FLOAT",
        "hose_fitment": "FLOAT",
        "flare_nut_tight": "FLOAT",
        "theory": "FLOAT",
        "total": "FLOAT",
        "re_test": "VARCHAR(50)",
        "exam_grade": "VARCHAR(50)",
        "trainer_name": "VARCHAR(255)",
        "sub_area": "VARCHAR(150)",
    }

    for column_name, column_type in trainee_extra_columns.items():
        if column_name not in trainee_columns:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    f'ALTER TABLE trainees ADD COLUMN "{column_name}" {column_type}'
                )

    # Refresh schema information after trainee migrations.
    inspector = inspect(engine)
    batch_columns = {col["name"] for col in inspector.get_columns("batches")}
    upload_history_columns = {col["name"] for col in inspector.get_columns("upload_history")}
    attendance_columns = {col["name"] for col in inspector.get_columns("attendance")}

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

    faculty_columns = {col["name"] for col in inspector.get_columns("faculty_sessions")}
    if "start_date" not in faculty_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE faculty_sessions ADD COLUMN start_date DATE")
    if "end_date" not in faculty_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE faculty_sessions ADD COLUMN end_date DATE")

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
                if "Day1:" in remarks:
                    try:
                        day1_part = remarks.split("Day1:")[1].split(";")[0].strip()
                        record.day1_status = day1_part if day1_part.lower() in {"present", "absent"} else "Absent"
                    except Exception:
                        record.day1_status = "Absent"
                if "Day2:" in remarks:
                    try:
                        day2_part = remarks.split("Day2:")[1].split(";")[0].strip()
                        record.day2_status = day2_part if day2_part.lower() in {"present", "absent"} else "Absent"
                    except Exception:
                        record.day2_status = "Absent"
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Migration warning: {e}")
    finally:
        session.close()
