from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Attendance, Batch, SessionLocal, Trainee, UploadHistory
from utils.excel import read_any_excel

attendance_bp = Blueprint("attendance", __name__)

REQUIRED_COLUMNS = ["Personal No", "Day1", "Day2"]


def normalize_status(value):
    return str(value).strip().lower()


def get_status_label(value):
    value = normalize_status(value)
    return "Present" if value in {"present", "p", "yes", "y", "1", "true"} else "Absent"



@attendance_bp.route("/master-preview", methods=["GET"])
def master_preview():
    batch_id = request.args.get("batch_id")
    if not batch_id:
        return jsonify({"error": "Batch ID is required"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        trainees = db.query(Trainee).filter(Trainee.batch_id == batch.id).all()
        preview_rows = []
        for trainee in trainees:
            attendance = trainee.attendance
            raw_day1 = attendance.day1_status if attendance and attendance.day1_status else trainee.day1
            raw_day2 = attendance.day2_status if attendance and attendance.day2_status else trainee.day2

            day1 = get_status_label(raw_day1)
            day2 = get_status_label(raw_day2)

            preview_rows.append(
                {
                    "trainee_id": trainee.id,
                    "name": trainee.name,
                    "personal_no": trainee.personal_no,
                    "day1": day1,
                    "day2": day2,
                }
            )

        return jsonify(
            {
                "preview": preview_rows,
                "total_rows": len(preview_rows),
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
                "source": "Master Sheet",
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


def matches_header(col_name, keywords):
    if not col_name:
        return False
    s = str(col_name).strip().lower().replace(" ", "").replace("_", "").replace(".", "").replace("-", "")
    return any(k in s for k in keywords)


def find_attendance_columns(df):
    cols = df.columns.tolist()

    pno_col = next((c for c in cols if matches_header(c, ["personalno", "pno", "empid", "employeeid", "traineeid", "persno"])), None)
    day1_col = next((c for c in cols if matches_header(c, ["day1", "d1"])), None)
    day2_col = next((c for c in cols if matches_header(c, ["day2", "d2"])), None)

    if not (pno_col and day1_col):
        for idx in range(min(5, len(df))):
            row_vals = df.iloc[idx].tolist()
            pno_temp = next((v for v in row_vals if matches_header(v, ["personalno", "pno", "empid", "employeeid", "traineeid", "persno"])), None)
            d1_temp = next((v for v in row_vals if matches_header(v, ["day1", "d1"])), None)
            if pno_temp and d1_temp:
                new_cols = [str(val).strip() for val in row_vals]
                df = df.iloc[idx + 1:].copy()
                df.columns = new_cols
                cols = new_cols
                pno_col = next((c for c in cols if matches_header(c, ["personalno", "pno", "empid", "employeeid", "traineeid", "persno"])), None)
                day1_col = next((c for c in cols if matches_header(c, ["day1", "d1"])), None)
                day2_col = next((c for c in cols if matches_header(c, ["day2", "d2"])), None)
                break

    name_col = next((c for c in cols if matches_header(c, ["name", "traineename", "studentname"])), None)
    return df, pno_col, day1_col, day2_col, name_col


@attendance_bp.route("/upload-preview", methods=["POST"])
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

    df, pno_col, day1_col, day2_col, name_col = find_attendance_columns(df)

    if not pno_col or not day1_col:
        found_cols = [str(c) for c in df.columns.tolist()[:8]]
        return jsonify(
            {
                "error": f"Excel file is missing required columns. Expected: Personal No (or P.NO.), Day1 (or Day 1), Day2. Found columns: {', '.join(found_cols)}"
            }
        ), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        preview_rows = []
        for _, row in df.iterrows():
            personal_no = str(row[pno_col]).strip() if pno_col and pd.notna(row[pno_col]) else ""
            if personal_no.endswith(".0"):
                personal_no = personal_no[:-2]

            day1 = str(row[day1_col]).strip() if day1_col and pd.notna(row[day1_col]) else ""
            day2 = str(row[day2_col]).strip() if day2_col and day2_col in df.columns and pd.notna(row[day2_col]) else ""
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
            name_val = trainee.name if trainee else (str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else "")

            preview_rows.append(
                {
                    "trainee_id": trainee.id if trainee else None,
                    "name": name_val,
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

            day1 = get_status_label(row.get("day1", ""))
            day2 = get_status_label(row.get("day2", ""))
            status = "Present" if day1 == "Present" or day2 == "Present" else "Absent"
            remarks = f"Day1: {day1}; Day2: {day2}"

            existing = db.query(Attendance).filter(Attendance.trainee_id == trainee.id).first()
            if existing:
                existing.day1_status = day1
                existing.day2_status = day2
                existing.status = status
                existing.remarks = remarks
                existing.attendance_date = datetime.utcnow().date()
            else:
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
        if batch_id:
            trainees = db.query(Trainee).filter(Trainee.batch_id == int(batch_id)).all()
        else:
            trainees = db.query(Trainee).all()

        day1_present = 0
        day1_absent = 0
        day2_present = 0
        day2_absent = 0
        total_present = 0
        total_absent = 0

        for trainee in trainees:
            attendance = trainee.attendance
            raw_day1 = (attendance.day1_status if attendance and attendance.day1_status else trainee.day1)
            raw_day2 = (attendance.day2_status if attendance and attendance.day2_status else trainee.day2)

            d1 = get_status_label(raw_day1)
            d2 = get_status_label(raw_day2)

            if d1 == "Present":
                day1_present += 1
                total_present += 1
            else:
                day1_absent += 1
                total_absent += 1

            if d2 == "Present":
                day2_present += 1
                total_present += 1
            else:
                day2_absent += 1
                total_absent += 1

        total_opportunities = len(trainees) * 2
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
