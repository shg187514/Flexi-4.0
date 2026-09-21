from datetime import datetime
from io import BytesIO

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, or_

from models import Attendance, Batch, DepartmentAllocation, FacultySession, PostTest, PreTest, SessionLocal, Trainee

report_bp = Blueprint("report", __name__)


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _get_day1_status(attendance):
    """Get Day1 attendance status from the attendance record."""
    if not attendance:
        return ""
    return attendance.day1_status or ""


def _get_day2_status(attendance):
    """Get Day2 attendance status from the attendance record."""
    if not attendance:
        return ""
    return attendance.day2_status or ""


def _build_preview_rows_for_report(db, report_type, from_date, to_date, batch_id, category, trainer_name=None, subject=None):
    if report_type == "complete_induction":
        query = db.query(Trainee, Batch, Attendance, PreTest, PostTest, DepartmentAllocation)
        query = query.outerjoin(Batch, Trainee.batch_id == Batch.id)
        query = query.outerjoin(Attendance, Attendance.trainee_id == Trainee.id)
        query = query.outerjoin(PreTest, PreTest.trainee_id == Trainee.id)
        query = query.outerjoin(PostTest, PostTest.trainee_id == Trainee.id)
        query = query.outerjoin(DepartmentAllocation, DepartmentAllocation.trainee_id == Trainee.id)
        if from_date:
            query = query.filter(Batch.start_date >= from_date)
        if to_date:
            query = query.filter(Batch.end_date <= to_date)
        if batch_id:
            query = query.filter(Trainee.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        rows = query.all()
        preview = []
        for trainee, batch, attendance, pre_test, post_test, department in rows:
            day1_status = _get_day1_status(attendance)
            day2_status = _get_day2_status(attendance)
            pre_score = pre_test.score if pre_test else ""
            post_score = post_test.score if post_test else ""
            improvement = ""
            if pre_score != "" and post_score != "":
                improvement = post_score - pre_score
            preview.append(
                {
                    "Name": trainee.name,
                    "Ticket No": getattr(trainee, "ticket_no", "") or trainee.personal_no,
                    "Personal No": trainee.personal_no,
                    "Batch": batch.batch_name if batch else "",
                    "Category": batch.category if batch else "",
                    "Day1 Attendance": day1_status,
                    "Day2 Attendance": day2_status,
                    "Pre-Test Marks": pre_score,
                    "Post-Test Marks": post_score,
                    "Improvement": improvement,
                    "Department": department.department if department else "",
                }
            )
        return preview

    if report_type == "attendance":
        query = db.query(Trainee, Batch, Attendance)
        query = query.outerjoin(Batch, Trainee.batch_id == Batch.id)
        query = query.outerjoin(Attendance, Attendance.trainee_id == Trainee.id)
        if from_date:
            query = query.filter(Batch.start_date >= from_date)
        if to_date:
            query = query.filter(Batch.end_date <= to_date)
        if batch_id:
            query = query.filter(Trainee.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        return [
            {
                "Name": trainee.name,
                "Personal No": trainee.personal_no,
                "Batch": batch.batch_name if batch else "",
                "Category": batch.category if batch else "",
                "Attendance Date": attendance.attendance_date.isoformat() if attendance and attendance.attendance_date else "",
                "Day1 Attendance": _get_day1_status(attendance),
                "Day2 Attendance": _get_day2_status(attendance),
            }
            for trainee, batch, attendance in query.all()
        ]

    if report_type in {"faculty", "trainer"}:
        query = db.query(FacultySession, Batch)
        query = query.outerjoin(Batch, FacultySession.batch_id == Batch.id)
        if from_date and to_date and from_date == to_date:
            single_d = from_date
            query = query.filter(
                or_(
                    FacultySession.start_date == single_d,
                    FacultySession.session_date == single_d,
                    Batch.start_date == single_d,
                )
            )
        else:
            if from_date:
                query = query.filter(
                    or_(
                        FacultySession.start_date >= from_date,
                        FacultySession.session_date >= from_date,
                        Batch.start_date >= from_date,
                    )
                )
            if to_date:
                query = query.filter(
                    or_(
                        FacultySession.end_date <= to_date,
                        FacultySession.session_date <= to_date,
                        Batch.end_date <= to_date,
                    )
                )
        if batch_id:
            query = query.filter(FacultySession.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        if trainer_name and str(trainer_name).strip():
            query = query.filter(FacultySession.faculty_name.ilike(f"%{str(trainer_name).strip()}%"))
        if subject and str(subject).strip():
            query = query.filter(FacultySession.topic.ilike(f"%{str(subject).strip()}%"))
        return [
            {
                "Trainer Name": session.faculty_name,
                "Batch": batch.batch_name if batch else "",
                "Category": batch.category if batch else "",
                "Start Date": session.start_date.isoformat() if session.start_date else (session.session_date.isoformat() if session.session_date else ""),
                "End Date": session.end_date.isoformat() if session.end_date else (session.session_date.isoformat() if session.session_date else ""),
                "Subject": session.topic,
                "Notes": session.notes or "",
            }
            for session, batch in query.all()
        ]

    if report_type == "pre_test":
        query = db.query(Trainee, Batch, PreTest)
        query = query.outerjoin(Batch, Trainee.batch_id == Batch.id)
        query = query.outerjoin(PreTest, PreTest.trainee_id == Trainee.id)
        if from_date:
            query = query.filter(Batch.start_date >= from_date)
        if to_date:
            query = query.filter(Batch.end_date <= to_date)
        if batch_id:
            query = query.filter(Trainee.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        return [
            {
                "Name": trainee.name,
                "Personal No": trainee.personal_no,
                "Batch": batch.batch_name if batch else "",
                "Category": batch.category if batch else "",
                "Pre-Test Marks": pre_test.score if pre_test else "",
                "Test Date": pre_test.test_date.isoformat() if pre_test and pre_test.test_date else "",
            }
            for trainee, batch, pre_test in query.all()
        ]

    if report_type == "post_test":
        query = db.query(Trainee, Batch, PostTest)
        query = query.outerjoin(Batch, Trainee.batch_id == Batch.id)
        query = query.outerjoin(PostTest, PostTest.trainee_id == Trainee.id)
        if from_date:
            query = query.filter(Batch.start_date >= from_date)
        if to_date:
            query = query.filter(Batch.end_date <= to_date)
        if batch_id:
            query = query.filter(Trainee.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        return [
            {
                "Name": trainee.name,
                "Personal No": trainee.personal_no,
                "Batch": batch.batch_name if batch else "",
                "Category": batch.category if batch else "",
                "Post-Test Marks": post_test.score if post_test else "",
                "Test Date": post_test.test_date.isoformat() if post_test and post_test.test_date else "",
            }
            for trainee, batch, post_test in query.all()
        ]

    if report_type == "department":
        query = db.query(Trainee, Batch, DepartmentAllocation)
        query = query.outerjoin(Batch, Trainee.batch_id == Batch.id)
        query = query.outerjoin(DepartmentAllocation, DepartmentAllocation.trainee_id == Trainee.id)
        if batch_id:
            query = query.filter(Trainee.batch_id == batch_id)
        if category:
            query = query.filter(Batch.category == category)
        return [
            {
                "Name": trainee.name,
                "Personal No": trainee.personal_no,
                "Batch": batch.batch_name if batch else "",
                "Category": batch.category if batch else "",
                "Department": department.department if department else "",
            }
            for trainee, batch, department in query.all()
        ]

    return []


@report_bp.route("/preview", methods=["POST"])
def preview_report():
    payload = request.get_json(silent=True) or {}
    report_type = payload.get("report_type")
    from_date = _parse_date(payload.get("from_date"))
    to_date = _parse_date(payload.get("to_date"))
    batch_id = payload.get("batch_id")
    category = payload.get("category")
    trainer_name = payload.get("trainer_name")
    subject = payload.get("subject")

    db = SessionLocal()
    try:
        preview = _build_preview_rows_for_report(
            db,
            report_type,
            from_date,
            to_date,
            batch_id,
            category,
            trainer_name=trainer_name,
            subject=subject,
        )
        if preview is None:
            return jsonify({"error": "Invalid report type"}), 400
        return jsonify({"rows": preview, "report_type": report_type}), 200
    finally:
        db.close()


@report_bp.route("/export/excel", methods=["POST"])
def export_excel():
    payload = request.get_json(silent=True) or {}
    report_type = payload.get("report_type")
    from_date = _parse_date(payload.get("from_date"))
    to_date = _parse_date(payload.get("to_date"))
    batch_id = payload.get("batch_id")
    category = payload.get("category")
    trainer_name = payload.get("trainer_name")
    subject = payload.get("subject")

    db = SessionLocal()
    try:
        rows = _get_rows_for_report(
            db,
            report_type,
            from_date,
            to_date,
            batch_id,
            category,
            trainer_name=trainer_name,
            subject=subject,
        )
        df = pd.DataFrame(rows)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")
        output.seek(0)
        return send_file(
            output,
            download_name=f"{report_type}_report.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    finally:
        db.close()


@report_bp.route("/export/pdf", methods=["POST"])
def export_pdf():
    payload = request.get_json(silent=True) or {}
    report_type = payload.get("report_type")
    from_date = _parse_date(payload.get("from_date"))
    to_date = _parse_date(payload.get("to_date"))
    batch_id = payload.get("batch_id")
    category = payload.get("category")
    trainer_name = payload.get("trainer_name")
    subject = payload.get("subject")

    db = SessionLocal()
    try:
        rows = _get_rows_for_report(
            db,
            report_type,
            from_date,
            to_date,
            batch_id,
            category,
            trainer_name=trainer_name,
            subject=subject,
        )
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        title = Paragraph(f"{report_type.replace('_', ' ').title()} Report", styles['Heading1'])
        elements = [title, Spacer(1, 12)]

        if rows:
            columns = list(rows[0].keys())
            table_data = [columns] + [list(row.values()) for row in rows]
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No data available", styles['BodyText']))

        doc.build(elements)
        output.seek(0)
        return send_file(output, download_name=f"{report_type}_report.pdf", as_attachment=True, mimetype="application/pdf")
    finally:
        db.close()


def _get_rows_for_report(db, report_type, from_date, to_date, batch_id, category, trainer_name=None, subject=None):
    return _build_preview_rows_for_report(
        db,
        report_type,
        from_date,
        to_date,
        batch_id,
        category,
        trainer_name=trainer_name,
        subject=subject,
    )
