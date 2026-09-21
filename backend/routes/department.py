from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Batch, DepartmentAllocation, SessionLocal, Trainee, UploadHistory
from utils.excel import read_any_excel

department_bp = Blueprint("department", __name__)
REQUIRED_COLUMNS = ["Personal No", "Department"]


@department_bp.route("", methods=["GET"])
def list_allocations():
    db = SessionLocal()
    try:
        allocations = db.query(DepartmentAllocation).all()
        return jsonify([
            {
                "id": a.id,
                "trainee_id": a.trainee_id,
                "department": a.department,
                "allocated_date": a.allocated_date.isoformat() if a.allocated_date else None,
                "remarks": a.remarks,
            }
            for a in allocations
        ]), 200
    finally:
        db.close()


@department_bp.route("/upload-preview", methods=["POST"])
def upload_preview():
    file = request.files.get("file")
    batch_id = request.form.get("batch_id")

    if not file:
        return jsonify({"error": "File is required"}), 400
    if not batch_id:
        return jsonify({"error": "Batch is required"}), 400

    try:
        df = read_any_excel(file)
    except Exception as e:
        return jsonify({"error": f"Unable to read Excel file: {e}"}), 400

    columns = [col.strip() for col in df.columns.tolist()]
    if any(col not in columns for col in REQUIRED_COLUMNS):
        return jsonify({"error": "Excel file must contain columns: Personal No, Department"}), 400

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
            department = row["Department"].strip()
            if not personal_no and not department:
                continue
            if not personal_no or not department:
                continue

            trainee = (
                db.query(Trainee)
                .filter(Trainee.batch_id == batch.id, Trainee.personal_no == personal_no)
                .first()
            )
            if not trainee:
                continue

            preview_rows.append(
                {
                    "trainee_id": trainee.id,
                    "name": trainee.name,
                    "personal_no": personal_no,
                    "department": department,
                }
            )

        history = UploadHistory(
            module_name="Department Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="department_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} department allocations",
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


@department_bp.route("/import", methods=["POST"])
def import_allocations():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id")
    rows = data.get("rows", [])
    file_name = data.get("file_name", "department_import")

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
            personal_no = str(row.get("personal_no", "")).strip()
            department = str(row.get("department", "")).strip()
            if not department:
                continue

            trainee = None
            if trainee_id:
                trainee = (
                    db.query(Trainee)
                    .filter(Trainee.id == int(trainee_id), Trainee.batch_id == batch.id)
                    .first()
                )
            else:
                trainee = (
                    db.query(Trainee)
                    .filter(Trainee.batch_id == batch.id, Trainee.personal_no == personal_no)
                    .first()
                )

            if not trainee:
                continue

            existing = db.query(DepartmentAllocation).filter(DepartmentAllocation.trainee_id == trainee.id).first()
            if existing:
                existing.department = department
                existing.allocated_date = datetime.utcnow().date()
                existing.remarks = "Updated from Excel"
            else:
                db.add(
                    DepartmentAllocation(
                        trainee_id=trainee.id,
                        department=department,
                        allocated_date=datetime.utcnow().date(),
                        remarks="Imported from Excel",
                    )
                )
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Department Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="department_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} department allocations",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Imported {imported_count} department allocations"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@department_bp.route("/upload-history", methods=["GET"])
def upload_history():
    db = SessionLocal()
    try:
        histories = db.query(UploadHistory).filter(UploadHistory.upload_type == "department_upload").order_by(UploadHistory.uploaded_at.desc()).all()
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


@department_bp.route("/upload-history/<int:history_id>", methods=["DELETE"])
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


@department_bp.route("/record/<int:trainee_id>", methods=["DELETE"])
def delete_department_record(trainee_id):
    db = SessionLocal()
    try:
        record = db.query(DepartmentAllocation).filter(DepartmentAllocation.trainee_id == trainee_id).first()
        if not record:
            return jsonify({"error": "Department allocation record not found"}), 404
        db.delete(record)
        db.commit()
        return jsonify({"message": "Department allocation record deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@department_bp.route("/summary", methods=["GET"])
def summary():
    batch_id = request.args.get("batch_id")
    db = SessionLocal()
    try:
        query = db.query(DepartmentAllocation).join(Trainee, DepartmentAllocation.trainee_id == Trainee.id)
        if batch_id:
            query = query.filter(Trainee.batch_id == int(batch_id))

        allocations = query.all()
        summary_map = {}
        for allocation in allocations:
            summary_map[allocation.department] = summary_map.get(allocation.department, 0) + 1

        return jsonify(
            {
                "total_allocations": len(allocations),
                "department_breakdown": summary_map,
            }
        ), 200
    finally:
        db.close()
