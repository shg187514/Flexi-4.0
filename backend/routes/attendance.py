from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Attendance, Batch, SessionLocal, Trainee, UploadHistory

attendance_bp = Blueprint("attendance", __name__)

REQUIRED_COLUMNS = ["Personal No", "Day1", "Day2"]


def normalize_status(value):
    return str(value).strip().lower()


def get_status_label(value):
    value = normalize_status(value)
    return "Present" if value in {"present", "p", "yes", "y", "1", "true"} else "Absent"


@attendance_bp.route("/upload-preview", methods=["POST"])
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
        return jsonify(
            {"error": "Excel file must contain columns: Personal No, Day1, Day2"}
        ), 400

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
            personal_no = row["Personal No"].strip()
            day1 = row["Day1"].strip()
            day2 = row["Day2"].strip()
            if not any([personal_no, day1, day2]):
                continue

            trainee = (
                db.query(Trainee)
                .filter(
                    Trainee.batch_id == batch.id,
                    Trainee.personal_no == personal_no,
                )
                .first()
            )
            if not trainee:
                continue

            preview_rows.append(
                {
                    "trainee_id": trainee.id,
                    "name": trainee.name,
                    "personal_no": personal_no,
                    "day1": day1,
                    "day2": day2,
                }
            )

        history = UploadHistory(
            module_name="Attendance Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="attendance_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} attendance records",
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return jsonify(
            {
                "preview": preview_rows,
                "total_rows": len(preview_rows),
                "upload_history_id": history.id,
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
            }
        ), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@attendance_bp.route("/import", methods=["POST"])
def import_attendance():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id")
    rows = data.get("rows", [])
    file_name = data.get("file_name", "attendance_import")

    if not batch_id or not rows:
        return jsonify({"error": "Batch and rows are required"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        imported_count = 0
        for row in rows:
            trainee_id = row.get("trainee_id")
            if not trainee_id:
                continue

            trainee = (
                db.query(Trainee)
                .filter(Trainee.id == int(trainee_id), Trainee.batch_id == batch.id)
                .first()
            )
            if not trainee:
                continue

            existing = db.query(Attendance).filter(Attendance.trainee_id == trainee.id).first()
            if existing:
                continue

            day1 = get_status_label(row.get("day1", ""))
            day2 = get_status_label(row.get("day2", ""))
            status = "Present" if day1 == "Present" or day2 == "Present" else "Absent"
            remarks = f"Day1: {day1}; Day2: {day2}"
            record = Attendance(
                trainee_id=trainee.id,
                attendance_date=datetime.utcnow().date(),
                day1_status=day1,
                day2_status=day2,
                status=status,
                remarks=remarks,
            )
            db.add(record)
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Attendance Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="attendance_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} attendance records",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Imported {imported_count} attendance records"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@attendance_bp.route("/upload-history", methods=["GET"])
def attendance_history():
    db = SessionLocal()
    try:
        histories = (
            db.query(UploadHistory)
            .filter(UploadHistory.upload_type == "attendance_upload")
            .order_by(UploadHistory.uploaded_at.desc())
            .all()
        )
        return jsonify(
            [
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
            ]
        ), 200
    finally:
        db.close()


@attendance_bp.route("/upload-history/<int:history_id>", methods=["DELETE"])
def delete_attendance_history(history_id):
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


@attendance_bp.route("/record/<int:trainee_id>", methods=["DELETE"])
def delete_attendance_record(trainee_id):
    db = SessionLocal()
    try:
        record = db.query(Attendance).filter(Attendance.trainee_id == trainee_id).first()
        if not record:
            return jsonify({"error": "Attendance record not found"}), 404
        db.delete(record)
        db.commit()
        return jsonify({"message": "Attendance record deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@attendance_bp.route("/summary", methods=["GET"])
def attendance_summary():
    batch_id = request.args.get("batch_id")
    db = SessionLocal()
    try:
        query = db.query(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        if batch_id:
            query = query.filter(Trainee.batch_id == int(batch_id))

        records = query.all()
        day1_present = 0
        day1_absent = 0
        day2_present = 0
        day2_absent = 0
        total_present = 0
        total_absent = 0

        for record in records:
            # Parse day1 status
            day1_status = (record.day1_status or "").strip().lower()
            if day1_status == "present":
                day1_present += 1
                total_present += 1
            elif day1_status == "absent":
                day1_absent += 1
                total_absent += 1

            # Parse day2 status
            day2_status = (record.day2_status or "").strip().lower()
            if day2_status == "present":
                day2_present += 1
                total_present += 1
            elif day2_status == "absent":
                day2_absent += 1
                total_absent += 1

        # Calculate total opportunities and attendance percentage
        total_opportunities = len(records) * 2  # 2 days per trainee
        attendance_percentage = (total_present / total_opportunities * 100) if total_opportunities > 0 else 0

        return jsonify(
            {
                "day1_present": day1_present,
                "day1_absent": day1_absent,
                "day2_present": day2_present,
                "day2_absent": day2_absent,
                "total_present": total_present,
                "total_absent": total_absent,
                "total_opportunities": total_opportunities,
                "attendance_percentage": round(attendance_percentage, 2),
            }
        ), 200
    finally:
        db.close()
