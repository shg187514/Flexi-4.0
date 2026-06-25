from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request
from models import Batch, PreTest, SessionLocal, Trainee, UploadHistory

pretest_bp = Blueprint("pretest", __name__)
REQUIRED_COLUMNS = ["Personal No", "Marks"]


@pretest_bp.route("", methods=["GET"])
def list_pretests():
    db = SessionLocal()
    try:
        records = db.query(PreTest).all()
        return jsonify([
            {
                "id": r.id,
                "trainee_id": r.trainee_id,
                "score": r.score,
                "test_date": r.test_date.isoformat() if r.test_date else None,
                "remarks": r.remarks,
            }
            for r in records
        ]), 200
    finally:
        db.close()


@pretest_bp.route("/upload-preview", methods=["POST"])
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
        return jsonify({"error": "Excel file must contain columns: Personal No, Marks"}), 400

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
            marks = row["Marks"].strip()
            if not personal_no and not marks:
                continue
            if not personal_no:
                continue

            trainee = (
                db.query(Trainee)
                .filter(Trainee.batch_id == batch.id, Trainee.personal_no == personal_no)
                .first()
            )
            if not trainee:
                continue

            try:
                score = int(float(marks)) if marks != "" else None
            except Exception:
                score = None

            preview_rows.append(
                {
                    "trainee_id": trainee.id,
                    "name": trainee.name,
                    "personal_no": personal_no,
                    "marks": marks,
                    "score": score,
                }
            )

        history = UploadHistory(
            module_name="Pre-Test Upload",
            batch_id=batch.id,
            file_name=file.filename,
            file_path="",
            upload_type="pretest_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=len(preview_rows),
            status="Previewed",
            notes=f"Previewed {len(preview_rows)} pre-test records",
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


@pretest_bp.route("/import", methods=["POST"])
def import_pretests():
    data = request.get_json(silent=True) or {}
    batch_id = data.get("batch_id")
    rows = data.get("rows", [])
    file_name = data.get("file_name", "pretest_import")

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
            marks = row.get("marks", "")
            if not trainee_id and not personal_no:
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

            try:
                score = int(float(marks))
            except Exception:
                continue

            existing = db.query(PreTest).filter(PreTest.trainee_id == trainee.id).first()
            if existing:
                existing.score = score
                existing.test_date = datetime.utcnow().date()
                existing.remarks = "Updated from Excel"
            else:
                db.add(
                    PreTest(
                        trainee_id=trainee.id,
                        score=score,
                        test_date=datetime.utcnow().date(),
                        remarks="Imported from Excel",
                    )
                )
            imported_count += 1

        db.flush()
        history = UploadHistory(
            module_name="Pre-Test Upload",
            batch_id=batch.id,
            file_name=file_name,
            file_path="",
            upload_type="pretest_upload",
            uploaded_by="system",
            uploaded_at=datetime.utcnow(),
            total_records=imported_count,
            status="Imported",
            notes=f"Imported {imported_count} pre-test records",
        )
        db.add(history)
        db.commit()
        return jsonify({"message": f"Imported {imported_count} pre-test records"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@pretest_bp.route("/upload-history", methods=["GET"])
def upload_history():
    db = SessionLocal()
    try:
        histories = db.query(UploadHistory).filter(UploadHistory.upload_type == "pretest_upload").order_by(UploadHistory.uploaded_at.desc()).all()
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


@pretest_bp.route("/upload-history/<int:history_id>", methods=["DELETE"])
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


@pretest_bp.route("/record/<int:trainee_id>", methods=["DELETE"])
def delete_pretest_record(trainee_id):
    db = SessionLocal()
    try:
        record = db.query(PreTest).filter(PreTest.trainee_id == trainee_id).first()
        if not record:
            return jsonify({"error": "Pre-test record not found"}), 404
        db.delete(record)
        db.commit()
        return jsonify({"message": "Pre-test record deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
