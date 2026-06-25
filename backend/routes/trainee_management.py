from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import func, case

from models import Trainee, Batch, Attendance, PreTest, PostTest, DepartmentAllocation, AuditTrail, SessionLocal

trainee_mgmt_bp = Blueprint("trainee_management", __name__)


def _record_audit(db, trainee_id, changed_field, old_value, new_value):
    """Record a change in the audit trail."""
    audit = AuditTrail(
        trainee_id=trainee_id,
        changed_field=changed_field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        changed_at=datetime.utcnow()
    )
    db.add(audit)
    db.commit()


@trainee_mgmt_bp.route("/search", methods=["GET"])
def search_trainees():
    """
    Search trainees by personal_no or name.
    Query params: personal_no, name (optional)
    """
    personal_no = request.args.get("personal_no", "").strip()
    name = request.args.get("name", "").strip()
    
    db = SessionLocal()
    try:
        query = db.query(Trainee).distinct()
        
        if personal_no:
            query = query.filter(Trainee.personal_no.ilike(f"%{personal_no}%"))
        if name:
            query = query.filter(Trainee.name.ilike(f"%{name}%"))
        
        if not personal_no and not name:
            return jsonify({"error": "Provide personal_no or name"}), 400
        
        trainees = query.all()
        result = []
        for trainee in trainees:
            result.append({
                "id": trainee.id,
                "personal_no": trainee.personal_no,
                "name": trainee.name,
                "ticket_no": trainee.ticket_no,
                "batch_id": trainee.batch_id,
                "batch_name": trainee.batch.batch_name if trainee.batch else ""
            })
        
        return jsonify({"trainees": result}), 200
    finally:
        db.close()


@trainee_mgmt_bp.route("/history/<personal_no>", methods=["GET"])
def get_trainee_history(personal_no):
    """
    Get complete trainee history (all batches attended).
    Returns trainee info and all batch records.
    """
    db = SessionLocal()
    try:
        trainees = db.query(Trainee).filter(Trainee.personal_no == personal_no).all()
        
        if not trainees:
            return jsonify({"error": "Trainee not found"}), 404
        
        # Get unique trainee info
        trainee_info = {
            "personal_no": trainees[0].personal_no,
            "name": trainees[0].name,
            "ticket_no": trainees[0].ticket_no,
        }
        
        # Fetch all batches for this trainee
        batches_data = []
        for trainee in trainees:
            batch = trainee.batch
            attendance = trainee.attendance
            pre_test = trainee.pre_test
            post_test = trainee.post_test
            department = trainee.department_allocation
            
            # Calculate attendance percentage
            attendance_percent = 0
            if attendance:
                present_days = 0
                if attendance.day1_status and attendance.day1_status.lower() == "present":
                    present_days += 1
                if attendance.day2_status and attendance.day2_status.lower() == "present":
                    present_days += 1
                attendance_percent = (present_days / 2) * 100 if present_days > 0 else 0
            
            # Calculate improvement
            improvement = None
            if pre_test and post_test:
                improvement = post_test.score - pre_test.score
            
            batches_data.append({
                "trainee_id": trainee.id,
                "batch_id": batch.id,
                "batch_name": batch.batch_name,
                "category": batch.category,
                "start_date": batch.start_date.isoformat() if batch.start_date else None,
                "end_date": batch.end_date.isoformat() if batch.end_date else None,
                "location": batch.location,
                "attendance_percent": round(attendance_percent, 2),
                "day1_status": attendance.day1_status if attendance else None,
                "day2_status": attendance.day2_status if attendance else None,
                "pre_test_marks": pre_test.score if pre_test else None,
                "post_test_marks": post_test.score if post_test else None,
                "improvement": improvement,
                "department": department.department if department else None,
            })
        
        return jsonify({
            "trainee_info": trainee_info,
            "batches": batches_data,
            "total_batches": len(batches_data)
        }), 200
    finally:
        db.close()


@trainee_mgmt_bp.route("/details/<int:trainee_id>", methods=["GET"])
def get_trainee_details(trainee_id):
    """
    Get detailed information for a specific trainee in a batch.
    """
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
        
        return jsonify({
            "id": trainee.id,
            "name": trainee.name,
            "ticket_no": trainee.ticket_no,
            "personal_no": trainee.personal_no,
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "category": batch.category,
            "start_date": batch.start_date.isoformat(),
            "end_date": batch.end_date.isoformat(),
            "location": batch.location,
            "day1_status": attendance.day1_status if attendance else None,
            "day2_status": attendance.day2_status if attendance else None,
            "pre_test_marks": pre_test.score if pre_test else None,
            "post_test_marks": post_test.score if post_test else None,
            "department": department.department if department else None,
        }), 200
    finally:
        db.close()


@trainee_mgmt_bp.route("/update/<int:trainee_id>", methods=["PUT"])
def update_trainee(trainee_id):
    """
    Update trainee details and record changes in audit trail.
    Allowed fields: name, ticket_no, category, day1_status, day2_status,
                   pre_test_marks, post_test_marks, department
    """
    payload = request.get_json(silent=True) or {}
    db = SessionLocal()
    
    try:
        trainee = db.query(Trainee).filter(Trainee.id == trainee_id).first()
        if not trainee:
            return jsonify({"error": "Trainee not found"}), 404
        
        # Update trainee name
        if "name" in payload:
            old_name = trainee.name
            trainee.name = payload["name"]
            if old_name != trainee.name:
                _record_audit(db, trainee_id, "name", old_name, trainee.name)
        
        # Update ticket number
        if "ticket_no" in payload:
            old_ticket = trainee.ticket_no
            trainee.ticket_no = payload["ticket_no"]
            if old_ticket != trainee.ticket_no:
                _record_audit(db, trainee_id, "ticket_no", old_ticket, trainee.ticket_no)
        
        # Update batch category
        if "category" in payload:
            batch = trainee.batch
            old_category = batch.category
            batch.category = payload["category"]
            if old_category != batch.category:
                _record_audit(db, trainee_id, "category", old_category, batch.category)
        
        # Update attendance
        if "day1_status" in payload:
            attendance = trainee.attendance
            if not attendance:
                attendance = Attendance(trainee_id=trainee_id)
                db.add(attendance)
            old_day1 = attendance.day1_status
            attendance.day1_status = payload["day1_status"]
            if old_day1 != attendance.day1_status:
                _record_audit(db, trainee_id, "day1_status", old_day1, attendance.day1_status)
        
        if "day2_status" in payload:
            attendance = trainee.attendance
            if not attendance:
                attendance = Attendance(trainee_id=trainee_id)
                db.add(attendance)
            old_day2 = attendance.day2_status
            attendance.day2_status = payload["day2_status"]
            if old_day2 != attendance.day2_status:
                _record_audit(db, trainee_id, "day2_status", old_day2, attendance.day2_status)
        
        # Update pre-test marks
        if "pre_test_marks" in payload:
            pre_test = trainee.pre_test
            if not pre_test:
                pre_test = PreTest(trainee_id=trainee_id, score=payload["pre_test_marks"])
                db.add(pre_test)
            else:
                old_score = pre_test.score
                pre_test.score = payload["pre_test_marks"]
                if old_score != pre_test.score:
                    _record_audit(db, trainee_id, "pre_test_marks", old_score, pre_test.score)
        
        # Update post-test marks
        if "post_test_marks" in payload:
            post_test = trainee.post_test
            if not post_test:
                post_test = PostTest(trainee_id=trainee_id, score=payload["post_test_marks"])
                db.add(post_test)
            else:
                old_score = post_test.score
                post_test.score = payload["post_test_marks"]
                if old_score != post_test.score:
                    _record_audit(db, trainee_id, "post_test_marks", old_score, post_test.score)
        
        # Update department
        if "department" in payload:
            department = trainee.department_allocation
            if not department:
                department = DepartmentAllocation(trainee_id=trainee_id, department=payload["department"])
                db.add(department)
            else:
                old_dept = department.department
                department.department = payload["department"]
                if old_dept != department.department:
                    _record_audit(db, trainee_id, "department", old_dept, department.department)
        
        db.commit()
        return jsonify({"message": "Trainee updated successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@trainee_mgmt_bp.route("/audit-trail/<int:trainee_id>", methods=["GET"])
def get_audit_trail(trainee_id):
    """
    Get audit trail for a specific trainee.
    """
    db = SessionLocal()
    try:
        trainee = db.query(Trainee).filter(Trainee.id == trainee_id).first()
        if not trainee:
            return jsonify({"error": "Trainee not found"}), 404
        
        audit_records = db.query(AuditTrail).filter(
            AuditTrail.trainee_id == trainee_id
        ).order_by(AuditTrail.changed_at.desc()).all()
        
        trail = []
        for record in audit_records:
            trail.append({
                "id": record.id,
                "field": record.changed_field,
                "old_value": record.old_value,
                "new_value": record.new_value,
                "changed_at": record.changed_at.isoformat(),
            })
        
        return jsonify({
            "trainee_id": trainee_id,
            "personal_no": trainee.personal_no,
            "name": trainee.name,
            "audit_trail": trail,
            "total_changes": len(trail)
        }), 200
    finally:
        db.close()
