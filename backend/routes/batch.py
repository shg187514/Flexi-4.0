from datetime import datetime

from flask import Blueprint, jsonify, request
from models import Attendance, Batch, DepartmentAllocation, FacultySession, PostTest, PreTest, SessionLocal, Trainee
from sqlalchemy import func, or_

batch_bp = Blueprint("batch", __name__)

ALLOWED_CATEGORIES = [
    "Temporary",
    "Guest",
    "Learn and Earn",
    "Diploma Apprentice",
    "Job Trainee",
]
ALLOWED_STATUSES = ["Active", "Completed"]


def _serialize_batch(batch):
    return {
        "id": batch.id,
        "batch_name": batch.batch_name,
        "category": batch.category,
        "start_date": batch.start_date.isoformat() if batch.start_date else None,
        "end_date": batch.end_date.isoformat() if batch.end_date else None,
        "location": batch.location,
        "coordinator_name": batch.coordinator_name,
        "status": batch.status,
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@batch_bp.route("", methods=["GET"])
def list_batches():
    db = SessionLocal()
    try:
        query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()

        batches_query = db.query(Batch)
        if query:
            batches_query = batches_query.filter(
                or_(
                    Batch.batch_name.ilike(f"%{query}%"),
                    Batch.location.ilike(f"%{query}%"),
                    Batch.coordinator_name.ilike(f"%{query}%"),
                )
            )
        if category:
            batches_query = batches_query.filter(Batch.category == category)
        if status:
            batches_query = batches_query.filter(Batch.status == status)

        batches = batches_query.order_by(Batch.id.desc()).all()
        return jsonify([_serialize_batch(b) for b in batches]), 200
    finally:
        db.close()


@batch_bp.route("", methods=["POST"])
def create_batch():
    payload = request.get_json(silent=True) or {}
    batch_name = (payload.get("batch_name") or "").strip()
    category = (payload.get("category") or "").strip()
    start_date = _parse_date(payload.get("start_date"))
    end_date = _parse_date(payload.get("end_date"))
    location = (payload.get("location") or "").strip()
    coordinator_name = (payload.get("coordinator_name") or "").strip()
    status = (payload.get("status") or "Active").strip()

    if not batch_name or not category or not start_date or not end_date or not location or not coordinator_name:
        return jsonify({"error": "All batch fields are required"}), 400
    if category not in ALLOWED_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    if end_date < start_date:
        return jsonify({"error": "End date cannot be earlier than start date"}), 400

    db = SessionLocal()
    try:
        existing = db.query(Batch).filter(Batch.batch_name == batch_name).first()
        if existing:
            return jsonify({"error": "Batch name already exists"}), 409
        batch = Batch(
            batch_name=batch_name,
            category=category,
            start_date=start_date,
            end_date=end_date,
            location=location,
            coordinator_name=coordinator_name,
            status=status,
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return jsonify(_serialize_batch(batch)), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["GET"])
def get_batch(batch_id):
    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404
        return jsonify(_serialize_batch(batch)), 200
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>/details", methods=["GET"])
def batch_details(batch_id):
    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        trainees = db.query(Trainee).filter(Trainee.batch_id == batch_id).all()
        trainee_ids = [trainee.id for trainee in trainees]

        attendance_uploaded = (
            db.query(Attendance)
            .join(Trainee, Attendance.trainee_id == Trainee.id)
            .filter(Trainee.batch_id == batch_id)
            .first() is not None
        )
        faculty_sessions_count = (
            db.query(FacultySession)
            .filter(FacultySession.batch_id == batch_id)
            .count()
        )
        pre_test_uploaded = (
            db.query(PreTest)
            .filter(PreTest.trainee_id.in_(trainee_ids))
            .first() is not None
        )
        post_test_uploaded = (
            db.query(PostTest)
            .filter(PostTest.trainee_id.in_(trainee_ids))
            .first() is not None
        )
        department_uploaded = (
            db.query(DepartmentAllocation)
            .filter(DepartmentAllocation.trainee_id.in_(trainee_ids))
            .first() is not None
        )

        return jsonify({
            "batch": _serialize_batch(batch),
            "statistics": {
                "total_trainees": len(trainees),
                "attendance_uploaded": attendance_uploaded,
                "faculty_sessions_count": faculty_sessions_count,
                "pre_test_uploaded": pre_test_uploaded,
                "post_test_uploaded": post_test_uploaded,
                "department_allocated": department_uploaded,
            },
        }), 200
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["PUT"])
def update_batch(batch_id):
    payload = request.get_json(silent=True) or {}
    batch_name = (payload.get("batch_name") or "").strip()
    category = (payload.get("category") or "").strip()
    start_date = _parse_date(payload.get("start_date"))
    end_date = _parse_date(payload.get("end_date"))
    location = (payload.get("location") or "").strip()
    coordinator_name = (payload.get("coordinator_name") or "").strip()
    status = (payload.get("status") or "Active").strip()

    if not batch_name or not category or not start_date or not end_date or not location or not coordinator_name:
        return jsonify({"error": "All batch fields are required"}), 400
    if category not in ALLOWED_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400
    if end_date < start_date:
        return jsonify({"error": "End date cannot be earlier than start date"}), 400

    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404

        duplicate = db.query(Batch).filter(Batch.batch_name == batch_name, Batch.id != batch_id).first()
        if duplicate:
            return jsonify({"error": "Batch name already exists"}), 409

        batch.batch_name = batch_name
        batch.category = category
        batch.start_date = start_date
        batch.end_date = end_date
        batch.location = location
        batch.coordinator_name = coordinator_name
        batch.status = status
        db.commit()
        db.refresh(batch)
        return jsonify(_serialize_batch(batch)), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["DELETE"])
def delete_batch(batch_id):
    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return jsonify({"error": "Batch not found"}), 404
        db.delete(batch)
        db.commit()
        return jsonify({"message": "Batch deleted successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@batch_bp.route("/dashboard", methods=["GET"])
def batch_dashboard():
    db = SessionLocal()
    try:
        total_batches = db.query(Batch).count()
        active_batches = db.query(Batch).filter(Batch.status == "Active").count()
        completed_batches = db.query(Batch).filter(Batch.status == "Completed").count()
        recent_batches = db.query(Batch).order_by(Batch.id.desc()).limit(5).all()

        category_counts = db.query(Batch.category, func.count(Batch.id)).group_by(Batch.category).all()
        category_breakdown = {category: count for category, count in category_counts}

        return jsonify({
            "total_batches": total_batches,
            "active_batches": active_batches,
            "completed_batches": completed_batches,
            "category_breakdown": category_breakdown,
            "recent_batches": [_serialize_batch(batch) for batch in recent_batches],
        }), 200
    finally:
        db.close()
