from datetime import datetime
from io import BytesIO
import math
import re

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import or_
from models import Batch, DepartmentAllocation, PostTest, PreTest, SessionLocal, Trainee, UploadHistory
from utils.excel import read_any_excel

trainee_bp = Blueprint("trainee", __name__)

# Columns expected from the new trainee Excel sheet.
# Header matching is normalized, so headers containing spaces/newlines work too.
EXCEL_COLUMNS = {
    "personal_no": "P.NO.",
    "name": "NAME",
    "gender": "Gender",
    "batch_name": "Batch",
    "grade": "Grade",
    "start_date": "Start Date",
    "end_date": "End Date",
    "day1": "DAY1",
    "day2": "DAY2",
    "day3": "DAY3",
    "day5": "DAY5",
    "day6": "DAY6",
    "bolt_tightening": "Bolt Tightening",
    "nut_tightening": "Nut Tightening",
    "screw_tightening": "Screw Tightening",
    "screw_grommet": "Screw Grommet",
    "plug_hole_grommet": "Plug Hole Grommet",
    "connector_connection": "Connector Connection",
    "hose_fitment": "Hose Fitment",
    "flare_nut_tight": "Flare Nut Tight",
    "theory": "Theory",
    "total": "Total",
    "re_test": "Re Test",
    "exam_grade": "Exam Grade",
    "trainer_name": "Trainer Name",
    "sub_area": "SUB AREA",
}


REQUIRED_EXCEL_COLUMNS = [
    "personal_no",
    "name",
    "batch_name",
    "start_date",
    "end_date",
]

NUMERIC_FIELDS = {
    "bolt_tightening",
    "nut_tightening",
    "screw_tightening",
    "screw_grommet",
    "plug_hole_grommet",
    "connector_connection",
    "hose_fitment",
    "flare_nut_tight",
    "theory",
    "total",
}


def normalize_header(value):
    """Normalize Excel headers so spaces, line breaks and punctuation are ignored."""
    value = str(value).replace("\n", " ").replace("\r", " ").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def clean_value(value):
    """Convert pandas/Excel values to JSON/database friendly values."""
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def clean_number(value):
    """Return a numeric Excel value as float, or None when blank/invalid."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_date(value):
    """Convert an Excel date to ISO format for the preview/import payload."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return ""
    if pd.isna(value):
        return ""
    try:
        return pd.to_datetime(value).date().isoformat()
    except Exception:
        return ""


def read_trainee_excel(file, password=None):
    """Read and normalize the complete trainee Excel sheet."""
    try:
        df = read_any_excel(file, password=password)
    except Exception as e:
        raise ValueError(f"Unable to read Excel file: {e}")

    # Normalize incoming headers once. This handles e.g. "Bolt \nTightening".
    normalized_headers = {normalize_header(col): col for col in df.columns}

    resolved = {}
    missing = []

    for key, expected_header in EXCEL_COLUMNS.items():
        source_column = normalized_headers.get(normalize_header(expected_header))
        if source_column is None:
            if key in REQUIRED_EXCEL_COLUMNS:
                missing.append(expected_header)
        else:
            resolved[key] = source_column

    if missing:
        raise ValueError("Excel file is missing columns: " + ", ".join(missing))

    preview_rows = []

    for _, source_row in df.iterrows():
        row = {}

        for key, source_column in resolved.items():
            value = source_row[source_column]
            if key in NUMERIC_FIELDS:
                row[key] = clean_number(value)
            elif key in {"start_date", "end_date"}:
                row[key] = clean_date(value)
            else:
                row[key] = clean_value(value)


        # Batch model compatibility:
        # Excel has Batch / Grade / Trainer Name / SUB AREA instead of the old
        # Batch Name / Category / Coordinator Name / Location fields.
        row["batch_name"] = clean_value(source_row[resolved["batch_name"]])
        row["category"] = row.get("grade", "")
        row["location"] = row.get("sub_area", "")
        row["coordinator_name"] = row.get("trainer_name", "")

        # Ignore completely empty rows.
        if not any(
            clean_value(row.get(field, ""))
            for field in ("personal_no", "name", "batch_name")
        ):
            continue

        preview_rows.append(row)

    if not preview_rows:
        raise ValueError("No valid data found in Excel file")

    return preview_rows


@trainee_bp.route("/search", methods=["GET"])
def search_trainees():
    query = request.args.get("q", "").strip()
    name = request.args.get("name", "").strip()
    personal_no = request.args.get("personal_no", "").strip()

    db = SessionLocal()
    try:
        filters = []
        if name:
            filters.append(Trainee.name.ilike(f"%{name}%"))
        if personal_no:
            filters.append(Trainee.personal_no.ilike(f"%{personal_no}%"))
        if query:
            filters.append(
                or_(
                    Trainee.name.ilike(f"%{query}%"),
                    Trainee.personal_no.ilike(f"%{query}%"),
                )
            )

        if filters:
            trainees = db.query(Trainee).filter(or_(*filters)).all()
        else:
            trainees = db.query(Trainee).all()

        response = []
        for t in trainees:
            batch = db.query(Batch).filter(Batch.id == t.batch_id).first()
            response.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "personal_no": t.personal_no,
                    "batch_id": t.batch_id,
                    "batch_name": batch.batch_name if batch else "",
                    "category": batch.category if batch else "",
                    "gender": t.gender,
                    "grade": t.grade,
                    "exam_grade": t.exam_grade,
                    "trainer_name": t.trainer_name,
                    "sub_area": t.sub_area,
                }
            )

        return jsonify(response), 200
    finally:
        db.close()


@trainee_bp.route("/download-template", methods=["GET"])
def download_template():
    template_df = pd.DataFrame(columns=list(EXCEL_COLUMNS.values()))

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="Trainees")

    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="trainee_upload_template.xlsx",
        as_attachment=True,
    )


@trainee_bp.route("/upload-preview", methods=["POST"])
def upload_preview():
    file = request.files.get("file")
    password = request.form.get("password")

    if not file:
        return jsonify({"error": "File is required"}), 400

    try:
        preview_rows = read_trainee_excel(file, password=password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Group information for batch preview.
    batches = {}
    for row in preview_rows:
        batch_name = row.get("batch_name", "")
        if not batch_name:
            continue

        if batch_name not in batches:
            batches[batch_name] = {
                "batch_name": batch_name,
                "category": row.get("category", ""),
                "start_date": row.get("start_date", ""),
                "end_date": row.get("end_date", ""),
                "location": row.get("location", ""),
                "coordinator_name": row.get("coordinator_name", ""),
                "trainee_count": 0,
            }

        batches[batch_name]["trainee_count"] += 1

    return jsonify(
        {
            "preview": preview_rows,
            "total_rows": len(preview_rows),
            "total_batches": len(batches),
            "batches": list(batches.values()),
            "file_name": file.filename,
            "columns": list(EXCEL_COLUMNS.values()),
        }
    ), 200


@trainee_bp.route("/import", methods=["POST"])
def import_trainees():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    file_name = data.get("file_name", "trainee_import")

    if not rows:
        return jsonify({"error": "Rows are required"}), 400

    db = SessionLocal()

    try:
        batches_data = {}

        for row in rows:
            batch_name = clean_value(row.get("batch_name", ""))
            if not batch_name:
                continue

            if batch_name not in batches_data:
                batches_data[batch_name] = {
                    "batch_name": batch_name,
                    "category": clean_value(row.get("category", "")),
                    "start_date": row.get("start_date"),
                    "end_date": row.get("end_date"),
                    "location": clean_value(row.get("location", "")),
                    "coordinator_name": clean_value(row.get("coordinator_name", "")),
                    "trainees": [],
                }

            batches_data[batch_name]["trainees"].append(row)

        if not batches_data:
            return jsonify({"error": "No valid batches found"}), 400

        total_imported = 0
        total_updated = 0
        created_batches = []
        updated_batches = []

        for batch_name, batch_data in batches_data.items():
            try:
                start_date = pd.to_datetime(batch_data["start_date"]).date()
                end_date = pd.to_datetime(batch_data["end_date"]).date()
            except Exception:
                return jsonify({"error": f"Invalid dates for batch: {batch_name}"}), 400

            if end_date < start_date:
                return jsonify(
                    {
                        "error": (
                            f"End Date cannot be earlier than Start Date "
                            f"for batch: {batch_name}"
                        )
                    }
                ), 400

            batch = (
                db.query(Batch)
                .filter(Batch.batch_name == batch_name)
                .first()
            )

            if batch:
                batch.category = batch_data["category"] or batch.category
                batch.start_date = start_date
                batch.end_date = end_date
                batch.location = batch_data["location"] or batch.location
                batch.coordinator_name = (
                    batch_data["coordinator_name"] or batch.coordinator_name
                )
                updated_batches.append(batch_name)
            else:
                batch = Batch(
                    batch_name=batch_name,
                    category=batch_data["category"] or "",
                    start_date=start_date,
                    end_date=end_date,
                    location=batch_data["location"] or "",
                    coordinator_name=batch_data["coordinator_name"] or "",
                    status="Active",
                )
                db.add(batch)
                db.flush()
                created_batches.append(batch_name)

            for row in batch_data["trainees"]:
                personal_no = clean_value(row.get("personal_no", ""))
                name = clean_value(row.get("name", ""))

                if not name or not personal_no:
                    continue

                existing_trainee = (
                    db.query(Trainee)
                    .filter(
                        Trainee.personal_no == personal_no,
                        Trainee.batch_id == batch.id,
                    )
                    .first()
                )

                trainee_values = {
                    "name": name,
                    "personal_no": personal_no,
                    "batch_id": batch.id,
                    "gender": clean_value(row.get("gender", "")) or None,
                    "grade": clean_value(row.get("grade", "")) or None,
                    "day1": clean_value(row.get("day1", "")) or None,
                    "day2": clean_value(row.get("day2", "")) or None,
                    "day3": clean_value(row.get("day3", "")) or None,
                    "day5": clean_value(row.get("day5", "")) or None,
                    "day6": clean_value(row.get("day6", "")) or None,
                    "bolt_tightening": clean_number(row.get("bolt_tightening")),
                    "nut_tightening": clean_number(row.get("nut_tightening")),
                    "screw_tightening": clean_number(row.get("screw_tightening")),
                    "screw_grommet": clean_number(row.get("screw_grommet")),
                    "plug_hole_grommet": clean_number(row.get("plug_hole_grommet")),
                    "connector_connection": clean_number(row.get("connector_connection")),
                    "hose_fitment": clean_number(row.get("hose_fitment")),
                    "flare_nut_tight": clean_number(row.get("flare_nut_tight")),
                    "theory": clean_number(row.get("theory")),
                    "total": clean_number(row.get("total")),
                    "re_test": clean_value(row.get("re_test", "")) or None,
                    "exam_grade": clean_value(row.get("exam_grade", "")) or None,
                    "trainer_name": clean_value(row.get("trainer_name", "")) or None,
                    "sub_area": clean_value(row.get("sub_area", "")) or None,
                }

                # Ticket No is not part of the new Excel sheet. The model still
                # requires it, so keep it blank unless an old-format column supplied it.
                if existing_trainee:
                    for key, value in trainee_values.items():
                        if key != "batch_id":
                            setattr(existing_trainee, key, value)
                    total_updated += 1
                else:
                    db.add(Trainee(**trainee_values))
                    total_imported += 1

            history = UploadHistory(
                module_name="Trainee Upload",
                batch_id=batch.id,
                file_name=file_name,
                file_path="",
                upload_type="trainee_upload",
                uploaded_by="system",
                uploaded_at=datetime.utcnow(),
                total_records=len(batch_data["trainees"]),
                status="Imported",
                notes=f"Imported trainees for batch {batch_name}",
            )
            db.add(history)

        db.commit()

        return jsonify(
            {
                "message": (
                    f"Import completed. {len(batches_data)} batches processed, "
                    f"{total_imported} trainees imported and "
                    f"{total_updated} trainees updated."
                ),
                "batches_created": created_batches,
                "batches_updated": updated_batches,
                "total_batches": len(batches_data),
                "total_trainees": total_imported,
                "total_updated": total_updated,
            }
        ), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        db.close()


@trainee_bp.route("/upload-history", methods=["GET"])
def trainee_upload_history():
    db = SessionLocal()
    try:
        histories = (
            db.query(UploadHistory)
            .filter(UploadHistory.upload_type == "trainee_upload")
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


@trainee_bp.route("/upload-history/<int:history_id>", methods=["DELETE"])
def delete_trainee_upload_history(history_id):
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


@trainee_bp.route("/<int:trainee_id>/profile", methods=["GET"])
def trainee_profile(trainee_id):
    from models import FacultySession
    db = SessionLocal()
    try:
        trainee = db.query(Trainee).filter(Trainee.id == trainee_id).first()
        if not trainee:
            return jsonify({"error": "Trainee not found"}), 404

        batch = trainee.batch
        attendance = trainee.attendance
        pre_test = trainee.pre_test
        post_test = trainee.post_test
        department = trainee.department_allocation

        attendance_percent = 0
        present_days = 0
        absent_days = 0
        day1_status = None
        day2_status = None

        if attendance:
            day1_status = attendance.day1_status
            day2_status = attendance.day2_status
            if day1_status and day1_status.lower() == "present":
                present_days += 1
            else:
                absent_days += 1
            if day2_status and day2_status.lower() == "present":
                present_days += 1
            else:
                absent_days += 1
            attendance_percent = (present_days / 2) * 100

        improvement = None
        if pre_test and post_test:
            improvement = post_test.score - pre_test.score

        faculty_sessions = []
        if batch:
            sessions = db.query(FacultySession).filter(FacultySession.batch_id == batch.id).all()
            faculty_sessions = [
                {
                    "id": s.id,
                    "faculty_name": s.faculty_name,
                    "topic": s.topic,
                    "session_date": s.session_date.isoformat() if s.session_date else None,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                }
                for s in sessions
            ]

        return jsonify(
            {
                "id": trainee.id,
                "name": trainee.name,
                "personal_no": trainee.personal_no,
                "gender": trainee.gender,
                "grade": trainee.grade,
                "day1": trainee.day1,
                "day2": trainee.day2,
                "day3": trainee.day3,
                "day5": trainee.day5,
                "day6": trainee.day6,
                "bolt_tightening": trainee.bolt_tightening,
                "nut_tightening": trainee.nut_tightening,
                "screw_tightening": trainee.screw_tightening,
                "screw_grommet": trainee.screw_grommet,
                "plug_hole_grommet": trainee.plug_hole_grommet,
                "connector_connection": trainee.connector_connection,
                "hose_fitment": trainee.hose_fitment,
                "flare_nut_tight": trainee.flare_nut_tight,
                "theory": trainee.theory,
                "total": trainee.total,
                "re_test": trainee.re_test,
                "exam_grade": trainee.exam_grade,
                "trainer_name": trainee.trainer_name,
                "sub_area": trainee.sub_area,
                "batch": {
                    "id": batch.id,
                    "batch_name": batch.batch_name,
                    "category": batch.category,
                    "start_date": batch.start_date.isoformat() if batch.start_date else None,
                    "end_date": batch.end_date.isoformat() if batch.end_date else None,
                    "location": batch.location if batch.location else None,
                    "coordinator_name": batch.coordinator_name if batch.coordinator_name else None,
                    "status": batch.status,
                }
                if batch
                else None,
                "attendance": {
                    "day1_status": day1_status,
                    "day2_status": day2_status,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "attendance_percent": round(attendance_percent, 2),
                    "attendance_date": attendance.attendance_date.isoformat() if attendance and attendance.attendance_date else None,
                    "remarks": attendance.remarks if attendance else None,
                },
                "pre_test": {
                    "score": pre_test.score if pre_test else None,
                    "test_date": pre_test.test_date.isoformat() if pre_test and pre_test.test_date else None,
                    "remarks": pre_test.remarks if pre_test else None,
                },
                "post_test": {
                    "score": post_test.score if post_test else None,
                    "test_date": post_test.test_date.isoformat() if post_test and post_test.test_date else None,
                    "remarks": post_test.remarks if post_test else None,
                },
                "improvement": improvement,
                "department": {
                    "department": department.department if department else None,
                    "allocated_date": department.allocated_date.isoformat() if department and department.allocated_date else None,
                    "remarks": department.remarks if department else None,
                },
                "faculty_sessions": faculty_sessions,
            }
        ), 200
    finally:
        db.close()


@trainee_bp.route("/<int:trainee_id>", methods=["DELETE"])
def delete_trainee(trainee_id):
    db = SessionLocal()
    try:
        trainee = db.query(Trainee).filter(Trainee.id == trainee_id).first()
        if not trainee:
            return jsonify({"error": "Trainee not found"}), 404
        db.delete(trainee)
        db.commit()
        return jsonify({"message": "Trainee deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
