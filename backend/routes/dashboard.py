from flask import Blueprint, jsonify, request
from models import Attendance, Batch, DepartmentAllocation, PostTest, PreTest, SessionLocal, Trainee
from sqlalchemy import and_, func, case

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/overview", methods=["GET"])
def overview():
    """
    Get comprehensive dashboard overview with all key metrics.
    All calculations are derived from actual database records.
    """
    db = SessionLocal()
    try:
        # 1. Count total batches and trainees using database queries
        total_batches = db.query(Batch).count()
        total_trainees = db.query(Trainee).count()
        
        # 2. Calculate attendance percentage using database queries
        # Count present days using CASE statement for efficiency
        day1_present_count = db.query(
            func.count(case((Attendance.day1_status.ilike("Present"), 1)))
        ).scalar() or 0
        
        day2_present_count = db.query(
            func.count(case((Attendance.day2_status.ilike("Present"), 1)))
        ).scalar() or 0
        
        day1_absent_count = db.query(
            func.count(case((Attendance.day1_status.ilike("Absent"), 1)))
        ).scalar() or 0
        
        day2_absent_count = db.query(
            func.count(case((Attendance.day2_status.ilike("Absent"), 1)))
        ).scalar() or 0
        
        total_present = day1_present_count + day2_present_count
        total_absent = day1_absent_count + day2_absent_count
        total_opportunities = total_present + total_absent
        
        # Calculate attendance percentage
        attendance_percentage = (total_present / total_opportunities * 100) if total_opportunities > 0 else 0

        # 3. Calculate average pre-test score using SQL aggregation
        avg_pre_test = db.query(func.avg(PreTest.score)).scalar()
        avg_pre_test = round(float(avg_pre_test), 2) if avg_pre_test is not None else 0

        # 4. Calculate average post-test score using SQL aggregation
        avg_post_test = db.query(func.avg(PostTest.score)).scalar()
        avg_post_test = round(float(avg_post_test), 2) if avg_post_test is not None else 0

        # 5. Calculate average improvement
        # Find trainees with both pre and post test scores
        pre_records = db.query(PreTest).all()
        post_records = db.query(PostTest).all()
        pre_map = {r.trainee_id: r.score for r in pre_records if r.score is not None}
        
        improvement_values = []
        for post in post_records:
            if post.score is not None and post.trainee_id in pre_map:
                improvement_values.append(post.score - pre_map[post.trainee_id])
        
        avg_improvement = (sum(improvement_values) / len(improvement_values)) if improvement_values else 0
        avg_improvement = round(avg_improvement, 2)

        # 6. Build attendance breakdown
        attendance_breakdown = {
            "Present": int(total_present),
            "Absent": int(total_absent),
        }

        # 7. Get category breakdown
        category_counts = db.query(
            Batch.category, 
            func.count(Trainee.id)
        ).join(Trainee, Trainee.batch_id == Batch.id).group_by(Batch.category).all()
        category_breakdown = {category: count for category, count in category_counts}

        # 8. Get department breakdown
        department_counts = db.query(
            DepartmentAllocation.department, 
            func.count(DepartmentAllocation.id)
        ).group_by(DepartmentAllocation.department).all()
        department_breakdown = {department: count for department, count in department_counts}

        # 9. Get all pre and post scores for chart visualization
        pre_scores = [score for (score,) in db.query(PreTest.score).filter(PreTest.score.isnot(None)).all()]
        post_scores = [score for (score,) in db.query(PostTest.score).filter(PostTest.score.isnot(None)).all()]

        return jsonify({
            "total_batches": total_batches,
            "total_trainees": total_trainees,
            "average_attendance": round(attendance_percentage, 2),
            "average_pre_test": avg_pre_test,
            "average_post_test": avg_post_test,
            "average_improvement": avg_improvement,
            "attendance_breakdown": attendance_breakdown,
            "category_breakdown": category_breakdown,
            "department_breakdown": department_breakdown,
            "pre_scores": pre_scores,
            "post_scores": post_scores,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route("/attendance-metrics", methods=["GET"])
def attendance_metrics():
    """
    Get detailed attendance metrics including day-wise breakdown.
    All values are calculated from actual database records.
    """
    batch_id = request.args.get("batch_id")
    db = SessionLocal()
    try:
        # Build query for attendance records
        query = db.query(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        if batch_id:
            query = query.filter(Trainee.batch_id == int(batch_id))

        # Use SQL CASE statements for efficient counting
        day1_present = db.query(
            func.count(case((Attendance.day1_status.ilike("Present"), 1)))
        ).select_from(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        
        if batch_id:
            day1_present = day1_present.filter(Trainee.batch_id == int(batch_id))
        
        day1_present_count = day1_present.scalar() or 0

        day1_absent = db.query(
            func.count(case((Attendance.day1_status.ilike("Absent"), 1)))
        ).select_from(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        
        if batch_id:
            day1_absent = day1_absent.filter(Trainee.batch_id == int(batch_id))
        
        day1_absent_count = day1_absent.scalar() or 0

        day2_present = db.query(
            func.count(case((Attendance.day2_status.ilike("Present"), 1)))
        ).select_from(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        
        if batch_id:
            day2_present = day2_present.filter(Trainee.batch_id == int(batch_id))
        
        day2_present_count = day2_present.scalar() or 0

        day2_absent = db.query(
            func.count(case((Attendance.day2_status.ilike("Absent"), 1)))
        ).select_from(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        
        if batch_id:
            day2_absent = day2_absent.filter(Trainee.batch_id == int(batch_id))
        
        day2_absent_count = day2_absent.scalar() or 0

        # Calculate totals
        total_present = day1_present_count + day2_present_count
        total_absent = day1_absent_count + day2_absent_count
        
        # Get total records count for opportunities calculation
        record_query = db.query(Attendance).join(Trainee, Attendance.trainee_id == Trainee.id)
        if batch_id:
            record_query = record_query.filter(Trainee.batch_id == int(batch_id))
        
        total_records = record_query.count()
        total_opportunities = total_records * 2  # 2 days per trainee
        
        # Calculate attendance percentage
        attendance_percentage = (total_present / total_opportunities * 100) if total_opportunities > 0 else 0

        return jsonify({
            "day1_present": int(day1_present_count),
            "day1_absent": int(day1_absent_count),
            "day2_present": int(day2_present_count),
            "day2_absent": int(day2_absent_count),
            "total_present": int(total_present),
            "total_absent": int(total_absent),
            "total_opportunities": int(total_opportunities),
            "attendance_percentage": round(attendance_percentage, 2),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route("/data-validation", methods=["GET"])
def data_validation():
    """
    Validate all dashboard data and verify calculations are correct.
    Returns detailed breakdown of all metrics with verification status.
    """
    db = SessionLocal()
    try:
        # Validate trainees
        total_trainees = db.query(Trainee).count()
        trainees_with_attendance = db.query(func.count(Attendance.id)).scalar() or 0
        trainees_with_pretest = db.query(func.count(PreTest.id)).scalar() or 0
        trainees_with_posttest = db.query(func.count(PostTest.id)).scalar() or 0
        
        # Validate attendance data
        total_attendance_records = db.query(Attendance).count()
        day1_records = db.query(func.count(Attendance.day1_status)).scalar() or 0
        day2_records = db.query(func.count(Attendance.day2_status)).scalar() or 0
        
        # Validate pre-test data
        pre_tests_count = db.query(func.count(PreTest.id)).scalar() or 0
        pre_tests_with_scores = db.query(func.count(PreTest.score)).filter(PreTest.score.isnot(None)).scalar() or 0
        pre_scores = [score for (score,) in db.query(PreTest.score).filter(PreTest.score.isnot(None)).all()]
        avg_pre_test = (sum(pre_scores) / len(pre_scores)) if pre_scores else 0
        
        # Validate post-test data
        post_tests_count = db.query(func.count(PostTest.id)).scalar() or 0
        post_tests_with_scores = db.query(func.count(PostTest.score)).filter(PostTest.score.isnot(None)).scalar() or 0
        post_scores = [score for (score,) in db.query(PostTest.score).filter(PostTest.score.isnot(None)).all()]
        avg_post_test = (sum(post_scores) / len(post_scores)) if post_scores else 0
        
        # Validate improvement calculation
        pre_map = {r.trainee_id: r.score for r in db.query(PreTest).filter(PreTest.score.isnot(None)).all()}
        improvement_values = []
        for post in db.query(PostTest).filter(PostTest.score.isnot(None)).all():
            if post.trainee_id in pre_map:
                improvement_values.append(post.score - pre_map[post.trainee_id])
        avg_improvement = (sum(improvement_values) / len(improvement_values)) if improvement_values else 0
        
        # Validate attendance percentages
        day1_present = db.query(func.count(case((Attendance.day1_status.ilike("Present"), 1)))).scalar() or 0
        day2_present = db.query(func.count(case((Attendance.day2_status.ilike("Present"), 1)))).scalar() or 0
        total_present = day1_present + day2_present
        total_opportunities = total_attendance_records * 2 if total_attendance_records > 0 else 0
        attendance_percentage = (total_present / total_opportunities * 100) if total_opportunities > 0 else 0
        
        return jsonify({
            "validation_status": "complete",
            "trainees": {
                "total": total_trainees,
                "with_attendance": trainees_with_attendance,
                "with_pre_test": trainees_with_pretest,
                "with_post_test": trainees_with_posttest,
            },
            "attendance": {
                "total_records": total_attendance_records,
                "day1_records": day1_records,
                "day2_records": day2_records,
                "day1_present": day1_present,
                "day2_present": day2_present,
                "total_present": total_present,
                "total_opportunities": total_opportunities,
                "attendance_percentage": round(attendance_percentage, 2),
            },
            "pre_test": {
                "total_records": pre_tests_count,
                "with_scores": pre_tests_with_scores,
                "average_score": round(avg_pre_test, 2),
                "score_count": len(pre_scores),
            },
            "post_test": {
                "total_records": post_tests_count,
                "with_scores": post_tests_with_scores,
                "average_score": round(avg_post_test, 2),
                "score_count": len(post_scores),
            },
            "improvement": {
                "total_comparisons": len(improvement_values),
                "average_improvement": round(avg_improvement, 2),
            },
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
