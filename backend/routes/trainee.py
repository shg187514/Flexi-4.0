from datetime import datetime
from io import BytesIO

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import or_
from models import Batch, DepartmentAllocation, PostTest, PreTest, SessionLocal, Trainee, UploadHistory

trainee_bp = Blueprint("trainee", __name__)
REQUIRED_COLUMNS = ["Name", "Ticket No", "Personal No"]


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
                    Trainee.ticket_no.ilike(f"%{query}%"),
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
                    "ticket_no": t.ticket_no,
                    "personal_no": t.personal_no,
                    "batch_id": t.batch_id,
                    "batch_name": batch.batch_name if batch else "",
                    "category": batch.category if batch else "",
                }
            )

        return jsonify(response), 200
    finally:
        db.close()


@trainee_bp.route("/download-template", methods=["GET"])
def download_template():
    template_df = pd.DataFrame(
        columns=["Name", "Ticket No", "Personal No"]
    )
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
            {"error": f"Excel file must contain columns: {', '.join(REQUIRED_COLUMNS)}"}
        ), 400

    normalized = df.rename(columns={col: col.strip() for col in df.columns})
    normalized = normalized[REQUIRED_COLUMNS].fillna("")
    normalized = normalized.astype(str)
    normalized = normalized.replace({"nan": "", "None": ""})

    preview_rows = []
    for _, row in normalized.iterrows():
        name = row["Name"].strip()
        ticket_no = row["Ticket No"].strip()
        personal_no = row["Personal No"].strip()
        if not any([name, ticket_no, personal_no]):
            continue
        preview_rows.append(
            {
                "name": name,
                "ticket_no": ticket_no,
                "personal_no": personal_no,
            }
        )

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        history = UploadHistory(
            module_name="Trainee Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="trainee_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} trainee records",
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return jsonify(
            {
                "preview": preview_rows,
                "total_rows": len(preview_rows),
                "upload_history_id": history.id,
                "file_name": file.filename,
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
            }
        ), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@trainee_bp.route("/import", methods=["POST"])
def import_trainees():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id")
    rows = data.get("rows", [])
    file_name = data.get("file_name", "trainee_import")

    if not batch_id or not rows:
        return jsonify({"error": "Batch and rows are required"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == int(batch_id)).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        imported_count = 0
        for row in rows:
            name = str(row.get("name", "")).strip()
            ticket_no = str(row.get("ticket_no", "")).strip()
            personal_no = str(row.get("personal_no", "")).strip()
            if not name or not ticket_no or not personal_no:
                continue

            exists = (
                db.query(Trainee)
                .filter(
                    (Trainee.personal_no == personal_no)
                    | (Trainee.ticket_no == ticket_no)
                )
                .first()
            )
            if exists:
                continue

            db.add(
                Trainee(
                    name=name,
                    ticket_no=ticket_no,
                    personal_no=personal_no,
                    batch_id=batch.id,
                )
            )
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Trainee Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="trainee_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} trainee records",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Imported {imported_count} trainee records"}), 201
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

        # Calculate attendance percentage
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

        # Get faculty sessions
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

        return jsonify({
            "id": trainee.id,
            "name": trainee.name,
            "ticket_no": trainee.ticket_no,
            "personal_no": trainee.personal_no,
            "batch": {
                "id": batch.id,
                "batch_name": batch.batch_name,
                "category": batch.category,
                "start_date": batch.start_date.isoformat() if batch.start_date else None,
                "end_date": batch.end_date.isoformat() if batch.end_date else None,
                "location": batch.location if batch.location else None,
                "coordinator_name": batch.coordinator_name if batch.coordinator_name else None,
                "status": batch.status,
            } if batch else None,
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
        }), 200
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
