import re
from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Batch, FacultySession, SessionLocal, UploadHistory
from utils.excel import read_any_excel

faculty_bp = Blueprint("faculty", __name__)
REQUIRED_COLUMNS = ["Start Date", "End Date", "Trainer Name", "Subject"]


def parse_date_val(val):
    if not val or pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in {"nan", "none", "nat"}:
        return None
    try:
        return pd.to_datetime(val_str).date()
    except Exception:
        return None


def faculty_to_dict(session):
    return {
        "id": session.id,
        "batch_id": session.batch_id,
        "faculty_name": session.faculty_name,
        "trainer_name": session.faculty_name,
        "start_date": session.start_date.isoformat() if session.start_date else (session.session_date.isoformat() if session.session_date else None),
        "end_date": session.end_date.isoformat() if session.end_date else (session.session_date.isoformat() if session.session_date else None),
        "topic": session.topic,
        "subject": session.topic,
        "notes": session.notes,
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
        start_date = parse_date_val(data.get("start_date"))
        end_date = parse_date_val(data.get("end_date"))
        trainer_name = data.get("trainer_name") or data.get("faculty_name") or ""
        subject = data.get("subject") or data.get("topic") or ""

        session = FacultySession(
            batch_id=data.get("batch_id"),
            faculty_name=trainer_name,
            start_date=start_date,
            end_date=end_date,
            session_date=start_date,
            topic=subject,
            notes=data.get("notes", ""),
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

        if "trainer_name" in data or "faculty_name" in data:
            session.faculty_name = data.get("trainer_name") or data.get("faculty_name") or session.faculty_name
        if "subject" in data or "topic" in data:
            session.topic = data.get("subject") or data.get("topic") or session.topic
        if "start_date" in data:
            session.start_date = parse_date_val(data["start_date"])
        if "end_date" in data:
            session.end_date = parse_date_val(data["end_date"])
        if "batch_id" in data:
            session.batch_id = data["batch_id"]
        if "notes" in data:
            session.notes = data["notes"]

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



def normalize_batch_str(val):
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"^batch\s*", "", s)
    if s.endswith(".0"):
        s = s[:-2]
    return s


@faculty_bp.route("/upload-preview", methods=["POST"])
def upload_preview():
    file = request.files.get("file")
    batch_id = request.form.get("batch_id")
    password = request.form.get("password")

    if not file:
        return jsonify({"error": "File is required"}), 400
    if not batch_id:
        return jsonify({"error": "Batch is required"}), 400

    try:
        df = read_any_excel(file, password=password)
    except Exception as e:
        return jsonify({"error": f"Unable to read Excel file: {e}"}), 400

    # Normalize column headers
    norm_map = {str(col).strip().lower().replace(" ", "").replace("_", ""): col for col in df.columns}

    start_date_col = norm_map.get("startdate") or norm_map.get("date")
    end_date_col = norm_map.get("enddate") or norm_map.get("date")
    trainer_col = norm_map.get("trainername") or norm_map.get("facultyname") or norm_map.get("trainer")
    subject_col = norm_map.get("subject") or norm_map.get("topic") or norm_map.get("subarea")
    batch_col = norm_map.get("batch") or norm_map.get("batchno") or norm_map.get("batchid") or norm_map.get("batchname")

    missing = []
    if not start_date_col and not end_date_col:
        missing.append("Start Date")
    if not trainer_col:
        missing.append("Trainer Name")

    if missing:
        return jsonify({"error": f"Excel file is missing required columns: {', '.join(missing)}"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        target_norm_name = normalize_batch_str(batch.batch_name)
        target_norm_id = str(batch.id)

        preview_rows = []
        for _, row in df.iterrows():
            # If batch column exists in Excel, filter rows that match the selected batch
            if batch_col:
                row_batch_str = str(row[batch_col]).strip() if pd.notna(row[batch_col]) else ""
                row_batch_norm = normalize_batch_str(row_batch_str)
                if row_batch_norm and target_norm_name:
                    if row_batch_norm != target_norm_name and row_batch_norm != target_norm_id and target_norm_name not in row_batch_norm:
                        continue

            start_val = str(row[start_date_col]).strip() if start_date_col and pd.notna(row[start_date_col]) else ""
            end_val = str(row[end_date_col]).strip() if end_date_col and pd.notna(row[end_date_col]) else ""
            trainer_val = str(row[trainer_col]).strip() if trainer_col and pd.notna(row[trainer_col]) else ""
            subject_val = str(row[subject_col]).strip() if subject_col and pd.notna(row[subject_col]) else ""

            if not any([start_val, end_val, trainer_val, subject_val]):
                continue

            parsed_start = parse_date_val(start_val)
            parsed_end = parse_date_val(end_val)

            preview_rows.append({
                "start_date": str(parsed_start) if parsed_start else start_val,
                "end_date": str(parsed_end) if parsed_end else (end_val or (str(parsed_start) if parsed_start else start_val)),
                "trainer_name": trainer_val or "Unassigned Trainer",
                "faculty_name": trainer_val or "Unassigned Trainer",
                "subject": subject_val or "General",
            })

        history = UploadHistory(
            module_name="Trainer Session Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="faculty_session_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} trainer sessions for {batch.batch_name}",
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
    file_name = data.get("file_name", "trainer_session_import")

    if not batch_id or not rows:
        return jsonify({"error": "Batch and rows are required"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        # Overwrite existing sessions for this batch upon re-importing
        db.query(FacultySession).filter(FacultySession.batch_id == batch.id).delete(synchronize_session=False)

        imported_count = 0
        for row in rows:
            trainer_name = str(row.get("trainer_name") or row.get("faculty_name") or "").strip() or "Unassigned Trainer"
            subject = str(row.get("subject") or row.get("topic") or "").strip() or "General"
            start_date_val = parse_date_val(row.get("start_date"))
            end_date_val = parse_date_val(row.get("end_date")) or start_date_val

            session = FacultySession(
                batch_id=batch.id,
                faculty_name=trainer_name,
                start_date=start_date_val,
                end_date=end_date_val,
                session_date=start_date_val,
                topic=subject,
                notes="",
            )
            db.add(session)
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Trainer Session Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="faculty_session_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} trainer sessions for {batch.batch_name}",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Successfully imported {imported_count} trainer sessions for {batch.batch_name}"}), 201
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
