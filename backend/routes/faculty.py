from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Batch, FacultySession, SessionLocal, UploadHistory

faculty_bp = Blueprint("faculty", __name__)
REQUIRED_COLUMNS = ["Date", "Faculty Name", "Subject", "Start Time", "End Time"]


def faculty_to_dict(session):
    return {
        "id": session.id,
        "batch_id": session.batch_id,
        "faculty_name": session.faculty_name,
        "session_date": session.session_date.isoformat() if session.session_date else None,
        "topic": session.topic,
        "notes": session.notes,
        "start_time": session.start_time if hasattr(session, 'start_time') else None,
        "end_time": session.end_time if hasattr(session, 'end_time') else None,
    }


@faculty_bp.route("", methods=["GET"])
def list_sessions():
    db = SessionLocal()
    try:
        sessions = db.query(FacultySession).all()
        return jsonify([faculty_to_dict(s) for s in sessions]), 200
    finally:
        db.close()


@faculty_bp.route("", methods=["POST"])
def create_session():
    data = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        session = FacultySession(
            batch_id=data.get("batch_id"),
            faculty_name=data.get("faculty_name"),
            session_date=data.get("session_date"),
            topic=data.get("subject"),
            notes=data.get("notes"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time")
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return jsonify(faculty_to_dict(session)), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@faculty_bp.route("/<int:session_id>", methods=["PUT"])
def update_session(session_id):
    data = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        session = db.query(FacultySession).filter(FacultySession.id == session_id).first()
        if not session:
            return jsonify({"error": "Session not found"}), 404
        for field in ["batch_id", "faculty_name", "session_date", "topic", "notes", "start_time", "end_time"]:
            if field in data:
                setattr(session, field, data[field])
        db.commit()
        db.refresh(session)
        return jsonify(faculty_to_dict(session)), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@faculty_bp.route("/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    db = SessionLocal()
    try:
        session = db.query(FacultySession).filter(FacultySession.id == session_id).first()
        if not session:
            return jsonify({"error": "Session not found"}), 404
        db.delete(session)
        db.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@faculty_bp.route("/upload-preview", methods=["POST"])
def upload_preview():
    file = request.files.get("file")
    batch_id = request.form.get("batch_id")
    if not file:
        return jsonify({"error": "File is required"}), 400
    if not batch_id:
        return jsonify({"error": "Batch is required"}), 400

    try:
        df = pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        return jsonify({"error": f"Unable to read Excel file: {e}"}), 400

    columns = [col.strip() for col in df.columns.tolist()]
    if any(col not in columns for col in REQUIRED_COLUMNS):
        return jsonify({"error": "Excel file must contain columns: Date, Faculty Name, Subject, Start Time, End Time"}), 400

    normalized = df.rename(columns={col: col.strip() for col in df.columns})
    normalized = normalized[REQUIRED_COLUMNS].fillna("")
    normalized = normalized.astype(str)
    normalized = normalized.replace({"nan": "", "None": ""})

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        preview_rows = []
        for _, row in normalized.iterrows():
            date_value = row["Date"].strip()
            faculty_name = row["Faculty Name"].strip()
            subject = row["Subject"].strip()
            start_time = row["Start Time"].strip()
            end_time = row["End Time"].strip()
            if not any([date_value, faculty_name, subject, start_time, end_time]):
                continue
            preview_rows.append({
                "date": date_value,
                "faculty_name": faculty_name,
                "subject": subject,
                "start_time": start_time,
                "end_time": end_time,
            })

        history = UploadHistory(
            module_name="Faculty Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="faculty_session_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} faculty sessions",
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return jsonify({
            "preview": preview_rows,
            "total_rows": len(preview_rows),
            "upload_history_id": history.id,
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@faculty_bp.route("/import", methods=["POST"])
def import_sessions():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id")
    rows = data.get("rows", [])
    file_name = data.get("file_name", "faculty_session_import")

    if not batch_id or not rows:
        return jsonify({"error": "Batch and rows are required"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        imported_count = 0
        for row in rows:
            date_value = row.get("date")
            faculty_name = row.get("faculty_name")
            subject = row.get("subject")
            start_time = row.get("start_time")
            end_time = row.get("end_time")
            if not faculty_name or not subject:
                continue

            session_date = None
            if date_value:
                try:
                    session_date = datetime.strptime(str(date_value), "%Y-%m-%d").date()
                except Exception:
                    try:
                        session_date = datetime.strptime(str(date_value), "%m/%d/%Y").date()
                    except Exception:
                        session_date = datetime.utcnow().date()

            session = FacultySession(
                batch_id=batch.id,
                faculty_name=faculty_name,
                session_date=session_date,
                topic=subject,
                notes="",
                start_time=start_time,
                end_time=end_time,
            )
            db.add(session)
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Faculty Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="faculty_session_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} faculty sessions",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Imported {imported_count} faculty sessions"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@faculty_bp.route("/upload-history", methods=["GET"])
def upload_history():
    db = SessionLocal()
    try:
        histories = db.query(UploadHistory).filter(UploadHistory.upload_type == "faculty_session_upload").order_by(UploadHistory.uploaded_at.desc()).all()
        return jsonify([
            {
                "id": h.id,
                "module_name": h.module_name,
                "batch_id": h.batch_id,
                "file_name": h.file_name,
                "upload_type": h.upload_type,
                "uploaded_by": h.uploaded_by,
                "uploaded_at": h.uploaded_at.isoformat() if h.uploaded_at else None,
                "total_records": h.total_records,
                "status": h.status,
                "notes": h.notes,
            }
            for h in histories
        ]), 200
    finally:
        db.close()


@faculty_bp.route("/upload-history/<int:history_id>", methods=["DELETE"])
def delete_upload_history(history_id):
    db = SessionLocal()
    try:
        history = db.query(UploadHistory).filter(UploadHistory.id == history_id).first()
        if not history:
            return jsonify({"error": "Upload history not found"}), 404
        db.delete(history)
        db.commit()
        return jsonify({"message": "Upload history deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
