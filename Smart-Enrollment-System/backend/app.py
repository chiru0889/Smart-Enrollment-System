from flask import (
    Flask, request, jsonify,
    send_from_directory, session, redirect
)

from flask import make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from datetime import date
from datetime import datetime
import os

import requests
import csv
from io import StringIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from flask import send_file

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch






# ================= PATH CONFIG =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")
JS_DIR = os.path.join(FRONTEND_DIR, "js")
CSS_DIR = os.path.join(FRONTEND_DIR, "css")

# ================= APP INIT =================

app = Flask(__name__)
app.config["SECRET_KEY"] = "analogica-secret-key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False

app.config["SQLALCHEMY_DATABASE_URI"] = \
    "mysql+pymysql://root:mysql123@localhost/certisured_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, supports_credentials=True)
Session(app)
db = SQLAlchemy(app)

# ================= MODELS =================

# 👤 MODEL: ADMIN (FOR LOGIN)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))


class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    course = db.Column(db.String(100))
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default="New")

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))   # ✅ ADD THIS
    program = db.Column(db.String(100))
    join_date = db.Column(db.Date)
    payment_type = db.Column(db.String(10))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="Active")
    # ✅ ADD THIS LINE
    emi_months = db.Column(db.Integer, default=0)

    

class EMI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer)
    emi_no = db.Column(db.Integer)
    amount = db.Column(db.Float)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="Pending")
    paid_date = db.Column(db.Date)

with app.app_context():
    db.create_all()

    # 🔐 TEMP: CREATE DEFAULT ADMIN (REMOVE AFTER FIRST RUN)
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin", password="admin123")
        db.session.add(admin)
        db.session.commit()

# ================= AUTH =================


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if data and data["username"] == "admin" and data["password"] == "admin123":
        session["admin_logged_in"] = True
        return jsonify(success=True)
    return jsonify(success=False), 401

@app.route("/api/logout")
def logout():
    session.clear()
    return jsonify(success=True)

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    username = data.get("username")
    new_password = data.get("new_password")

    admin = Admin.query.filter_by(username=username).first()

    if not admin:
        return jsonify(error="Admin not found"), 404

    admin.password = new_password
    db.session.commit()

    return jsonify(success=True)



@app.route("/api/protected")
def protected():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401
    return jsonify(message="OK")

# ================= DASHBOARD =================

@app.route("/api/dashboard/stats")
def dashboard_stats():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    active_enquiries = Enquiry.query.count()
    active_enrollments = Enrollment.query.filter_by(status="Active").count()

    stats = db.session.get(EnquiryStats, 1)
    total_created = stats.total_enquiries if stats else active_enquiries

    dropped = total_created - active_enquiries
    if dropped < 0:
        dropped = 0

    return jsonify(
        totalEnquiries=active_enquiries,   # ✅ ONLY ACTIVE
        totalEnrollments=active_enrollments,
        totalDropouts=dropped
    )






@app.route("/api/dashboard/funnel")
def dashboard_funnel():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    stats = db.session.get(EnquiryStats, 1)
    total_created = stats.total_enquiries if stats else 0

    active_enquiries = Enquiry.query.count()
    active_enrollments = Enrollment.query.filter_by(status="Active").count()

    dropped = total_created - (active_enquiries + active_enrollments)
    if dropped < 0:
        dropped = 0

    return jsonify(
        labels=["Enquiries", "Enrollments", "Dropouts"],
        data=[
            active_enquiries,
            active_enrollments,
            dropped   # ✅ FIXED (this updates graph)
        ]
    )


@app.route("/api/dashboard/recent")
def dashboard_recent():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    recent = Enrollment.query.order_by(
        Enrollment.id.desc()
    ).limit(5).all()

    return jsonify([{
        "name": e.name,
        "program": e.program,
        "date": e.join_date.strftime("%d %b %Y") if e.join_date else "-"
    } for e in recent])

# ================= ENQUIRIES =================

class EnquiryStats(db.Model):
    __tablename__ = "enquiry_stats"

    id = db.Column(db.Integer, primary_key=True)
    total_enquiries = db.Column(db.Integer, nullable=False, default=0)

@app.route("/api/enquiries")
def api_enquiries():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    return jsonify([{
        "id": e.id,
        "name": e.name,
        "phone": e.phone,     # ✅ ADD THIS LINE
        "email": e.email,
        "course": e.course,
        "reason": e.reason,
        "status": e.status
    } for e in Enquiry.query.all()])


@app.route("/api/enquiry/convert", methods=["POST"])
def convert_enquiry():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    enquiry_id = data.get("id")

    enquiry = db.session.get(Enquiry, enquiry_id)
    if not enquiry:
        return jsonify(error="Enquiry not found"), 404

    enrollment = Enrollment(
        name=enquiry.name,
        email=enquiry.email,
        phone=enquiry.phone if enquiry.phone else None,   # ✅ USE IT HERE
        program=enquiry.course,
        join_date=date.today(),
        payment_type="",
        amount=None,
        status="Active"
    )

    db.session.add(enrollment)
    db.session.delete(enquiry)
    db.session.commit()

    return jsonify(success=True)



@app.route("/api/enquiry/drop", methods=["POST"])
def drop_enquiry():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    enquiry_id = data.get("id")

    enquiry = db.session.get(Enquiry, enquiry_id)

    print("Enquiry phone before conversion:", enquiry.phone)

    if not enquiry:
        return jsonify(error="Enquiry not found"), 404

    db.session.delete(enquiry)
    db.session.commit()

    return jsonify(success=True)

@app.route("/api/enquiry/add", methods=["POST"])
def add_enquiry():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()

    new_enquiry = Enquiry(
        name=data.get("name"),
        phone=data.get("phone"),      # ✅ ADD THIS LINE
        email=data.get("email"),
        course=data.get("course"),
        status="Enquiry"
    )

    db.session.add(new_enquiry)

    stats = db.session.get(EnquiryStats, 1)
    if stats:
        stats.total_enquiries += 1
    else:
        stats = EnquiryStats(id=1, total_enquiries=1)
        db.session.add(stats)

    db.session.commit()

    return jsonify(success=True)


@app.route("/api/emi/undo", methods=["POST"])
def undo_emi_payment():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.json

    emi = EMI.query.filter_by(
        enrollment_id=data.get("enrollment_id"),
        emi_no=data.get("emi_no")
    ).first()

    if not emi:
        return jsonify(error="Not found"), 404

    emi.status = "Pending"

    db.session.commit()

    return jsonify(success=True)



@app.route("/api/enquiries/upload-csv", methods=["POST"])
def upload_enquiry_csv():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    if "file" not in request.files:
        return jsonify(error="No file uploaded"), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="Empty file"), 400

    import csv
    from io import StringIO

    # ✅ FIX 1: Remove BOM
    stream = StringIO(file.stream.read().decode("utf-8-sig"))
    reader = csv.DictReader(stream)

    added = 0
    skipped = 0

    for row in reader:

        # ✅ FIX 2: Convert all keys to lowercase automatically
        row = {k.lower(): v for k, v in row.items()}

        print("CLEAN ROW:", row)

        name = row.get("name")
        phone = row.get("phone")

        if not name or not phone:
            skipped += 1
            continue

        phone = phone.strip()

        if not phone.isdigit() or len(phone) != 10:
            skipped += 1
            continue

        existing = Enquiry.query.filter_by(phone=phone).first()
        if existing:
            skipped += 1
            continue

        enquiry = Enquiry(
            name=name,
            email=row.get("email") or "",
            phone=phone,
            course=row.get("course") or "",
            reason=row.get("reason") or "",
            status="Enquiry"
        )

        db.session.add(enquiry)
        added += 1

    db.session.commit()

    return jsonify(success=True, added=added, skipped=skipped)

@app.route("/api/enquiry/reason", methods=["POST"])
def add_reason():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.json

    enquiry = db.session.get(Enquiry, data.get("id"))

    if not enquiry:
        return jsonify(error="Not found"), 404

    enquiry.reason = data.get("reason")  # only update reason
    db.session.commit()

    return jsonify(success=True)


@app.route("/api/enquiries/import-sheet", methods=["POST"])
def import_from_google_sheet():

    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    sheet_url = data.get("url")
    # ✅ AUTO-CONVERT GOOGLE SHEET LINK
    if "docs.google.com" in sheet_url and "/edit" in sheet_url:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    if not sheet_url:
        return jsonify(error="Sheet URL required"), 400

    try:
        response = requests.get(sheet_url)
        content = response.content.decode("utf-8")

        reader = csv.DictReader(StringIO(content))
        # ✅ ADD THIS LINE HERE
        print("HEADERS:", reader.fieldnames)

        added = 0

        for row in reader:
            # ✅ ALSO ADD THIS INSIDE LOOP
            print("ROW:", row)
            name = row.get("Name") or row.get("name")
            phone = row.get("Phone") or row.get("phone")

            if not name or not phone:
                continue

            existing = Enquiry.query.filter_by(phone=phone).first()
            if existing:
                continue

            enquiry = Enquiry(
                name=name,
                phone=phone,
                email=row.get("Email") or "",
                course=row.get("Course") or "",
                reason="",
                status="Enquiry"
            )

            db.session.add(enquiry)
            added += 1

        db.session.commit()

        return jsonify(success=True, added=added)

    except Exception as e:
        return jsonify(error=str(e)), 500




# ================= ENROLLMENTS =================

@app.route("/api/enrollments")
def api_enrollments():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    result = []
    for e in Enrollment.query.all():
        result.append({
            "id": e.id,
            "name": e.name,
            "program": e.program,
            "join_date": e.join_date.strftime("%Y-%m-%d") if e.join_date else "",
            "payment_type": e.payment_type,
            "amount": e.amount,
            "emi_total": EMI.query.filter_by(enrollment_id=e.id).count(),
            "emi_paid": EMI.query.filter_by(
                enrollment_id=e.id, status="Paid"
            ).count(),
            "status": e.status,
            
        })
    return jsonify(result)


# ================= ADD ENROLLMENT =================

@app.route("/api/enrollment/add", methods=["POST"])
def add_enrollment():
    if not session.get("admin_logged_in"):
        return jsonify(success=False, message="Unauthorized"), 401

    data = request.get_json()

    if not data.get("name") or not data.get("email") or not data.get("program"):
        return jsonify(success=False, message="Missing required fields"), 400

    join_date = None
    if data.get("date"):
        join_date = date.fromisoformat(data["date"])

    amount = data.get("amount")

    enrollment = Enrollment(
        name=data.get("name").strip(),
        email=data.get("email").strip(),
         phone=data.get("phone"),   # ✅ CORRECT HERE
        program=data.get("program").strip(),
        join_date=join_date,
        payment_type=data.get("payment_type"),
        amount=float(amount) if amount not in (None, "", "null") else None,
        status="Active"
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify(success=True, enrollment_id=enrollment.id)

# ================= UPDATE ENROLLMENT =================

@app.route("/api/enrollment/update", methods=["POST"])
def update_enrollment():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    enrollment = db.session.get(Enrollment, data.get("id"))

    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    enrollment.name = data.get("name", enrollment.name)
    db.session.commit()

    return jsonify(success=True)

# ================= DELETE ENROLLMENT =================

@app.route("/api/enrollment/delete", methods=["POST"])
def delete_enrollment():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    enrollment = db.session.get(Enrollment, data.get("id"))

    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    EMI.query.filter_by(enrollment_id=enrollment.id).delete()
    db.session.delete(enrollment)
    db.session.commit()

    return jsonify(success=True)

@app.route("/api/enrollment/set-payment", methods=["POST"])
def set_payment_type():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()
    enrollment_id = data.get("id")
    payment_type = data.get("payment_type")
    amount = data.get("amount")

    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    enrollment.payment_type = payment_type
    enrollment.amount = amount

    db.session.commit()
    return jsonify(success=True)

# ================= EMI =================
from dateutil.relativedelta import relativedelta
from datetime import date

@app.route("/api/emi/generate", methods=["POST"])
def generate_emi():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()

    enrollment_id = int(data.get("enrollment_id"))
    months = int(data.get("months"))
    start_date = date.fromisoformat(data.get("start_date"))

    # OPTIONAL: new amount (only if admin changed it)
    new_amount = data.get("amount")

    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    if enrollment.payment_type != "EMI":
        return jsonify(error="Not an EMI enrollment"), 400
    
    enrollment.emi_months = months

    # ✅ UPDATE AMOUNT ONLY IF ADMIN SENT IT
    if new_amount is not None:
        enrollment.amount = float(new_amount)

    # 🔥 DELETE OLD EMI PLAN (Prevents duplicate)
    EMI.query.filter_by(enrollment_id=enrollment_id).delete()
    db.session.commit()

    # ✅ CALCULATE EMI USING CURRENT ENROLLMENT AMOUNT
    emi_amount = round(enrollment.amount / months, 2)

    current_date = start_date  # Start from selected date

    for i in range(months):
        emi = EMI(
            enrollment_id=enrollment_id,
            emi_no=i + 1,
            amount=emi_amount,
            due_date=current_date,
            status="Pending"
        )

        db.session.add(emi)

        # 🔥 Move to next month (THIS FIXES DUPLICATE DATE ISSUE)
        current_date = current_date + relativedelta(months=1)

    db.session.commit()

    return jsonify(
        success=True,
        months=months,
        total_amount=enrollment.amount
    )

@app.route("/api/emi")
def api_emi():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    today = date.today()
    result = []

    # ✅ ONLY ACTIVE EMI STUDENTS
    enrollments = Enrollment.query.filter_by(
        payment_type="EMI",
        status="Active"
    ).all()

    for enroll in enrollments:
        emis = EMI.query.filter_by(
            enrollment_id=enroll.id
        ).order_by(EMI.emi_no).all()

        if not emis:
            result.append({
                "enrollment_id": enroll.id,
                "student": enroll.name,
                "program": enroll.program,
                "emi_no": 0,
                "amount": 0,
                "due_date": "",
                "status": "Not Generated"
            })
            continue

        for e in emis:
            if e.due_date and e.due_date < today and e.status != "Paid":
                e.status = "Overdue"

            result.append({
                "enrollment_id": enroll.id,
                "student": enroll.name,
                "program": enroll.program,
                "emi_no": e.emi_no,
                "amount": e.amount,
                "due_date": e.due_date.strftime("%Y-%m-%d"),
                "status": e.status,
                "paid_date": e.paid_date.strftime("%Y-%m-%d") if e.paid_date else None  # ✅ ADDED ONLY THIS LINE
            })

    db.session.commit()
    return jsonify(result)


# ================= OVERDUE EMI =================

@app.route("/api/emi/overdue")
def overdue_emi():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    today = date.today()

    for e in EMI.query.all():
        if e.due_date and e.due_date < today and e.status != "Paid":
            e.status = "Overdue"

    db.session.commit()

    overdue = EMI.query.filter_by(status="Overdue").all()
    result = []

    for e in overdue:
        enroll = db.session.get(Enrollment, e.enrollment_id)
        result.append({
            "enrollment_id": e.enrollment_id,
            "student": enroll.name if enroll else "Unknown",
            "program": enroll.program if enroll else "Unknown",
            "emi_no": e.emi_no,
            "amount": e.amount,
            "due_date": e.due_date.strftime("%Y-%m-%d") if e.due_date else "",
            "status": e.status
        })

    return jsonify(result)

@app.route("/api/overdue/download-report")
def download_overdue_report():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    from io import BytesIO
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesizes.A4
    )

    elements = []
    styles = getSampleStyleSheet()

    # 🎯 Title
    title_style = styles["Heading1"]
    elements.append(Paragraph("Overdue EMI Report", title_style))
    elements.append(Spacer(1, 0.3 * inch))

    today = date.today()
    overdue_emis = EMI.query.filter(EMI.status == "Overdue").all()

    data = [["Student Name", "Amount", "Days Late", "Fine"]]

    total_due = 0
    total_fine = 0

    for e in overdue_emis:
        days_late = (today - e.due_date).days if e.due_date else 0
        fine = days_late * 50

        total_due += e.amount
        total_fine += fine

        enrollment = db.session.get(Enrollment, e.enrollment_id)

        student_name = enrollment.name if enrollment else "Unknown"

        data.append([
            student_name,
            f"₹{e.amount}",
            str(days_late),
            f"₹{fine}"
])
    # 🎯 Totals Row
    data.append(["", "", "Total Due", f"₹{total_due}"])
    data.append(["", "", "Total Fine", f"₹{total_fine}"])
    data.append(["", "", "Grand Total", f"₹{total_due + total_fine}"])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -4), colors.whitesmoke),
        ("BACKGROUND", (0, -3), (-1, -1), colors.HexColor("#FDE68A")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Overdue_Report.pdf",
        mimetype="application/pdf"
    )

# ================= PAY EMI =================

from datetime import date   # make sure this is imported at top

@app.route("/api/emi/pay", methods=["POST"])
def pay_emi():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    data = request.get_json()

    emi = EMI.query.filter_by(
        enrollment_id=data.get("enrollment_id"),
        emi_no=data.get("emi_no")
    ).first()

    if not emi:
        return jsonify(error="EMI not found"), 404

    emi.status = "Paid"
    emi.paid_date = date.today()   # ✅ SAVE PAID DATE HERE

    db.session.commit()

    return jsonify(success=True)
# ================= STUDENT EMI =================

@app.route("/api/student/emi/<int:enroll_id>")
def student_emi(enroll_id):
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    emis = EMI.query.filter_by(enrollment_id=enroll_id).all()

    return jsonify([{
        "emi_no": e.emi_no,
        "amount": e.amount,
        "due_date": e.due_date.strftime("%Y-%m-%d") if e.due_date else "",
        "status": e.status
    } for e in emis])

# ================= STUDENT DETAILS =================

@app.route("/api/student/<int:enroll_id>")
def student_details(enroll_id):
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    enrollment = db.session.get(Enrollment, enroll_id)
    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    emis = EMI.query.filter(
        EMI.enrollment_id == enroll_id
    ).order_by(EMI.emi_no.asc()).all()

    return jsonify({
        "id": enrollment.id,
        "name": enrollment.name,
        "email": enrollment.email,
        "phone": enrollment.phone,
        "program": enrollment.program,
        "join_date": enrollment.join_date.strftime("%Y-%m-%d")
            if enrollment.join_date else "",
        "payment_type": enrollment.payment_type,
        "amount": enrollment.amount,
        "status": enrollment.status,
         # ✅ ADD THIS LINE
        "emi_months": enrollment.emi_months,
        "emis": [
            {
                "emi_no": e.emi_no,
                "amount": e.amount,
                "due_date": e.due_date.strftime("%Y-%m-%d")
                    if e.due_date else "",
                "status": e.status,
                "paid_date": e.paid_date.strftime("%Y-%m-%d")
                    if e.paid_date else None
            }
            for e in emis
        ]
    })



# ================= DOWNLOAD STUDENT REPORT =================





@app.route("/api/student/report/pdf/<int:enroll_id>")
def download_student_report_pdf(enroll_id):
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    from io import BytesIO

    enrollment = db.session.get(Enrollment, enroll_id)
    if not enrollment:
        return jsonify(error="Enrollment not found"), 404

    emis = EMI.query.filter_by(
        enrollment_id=enroll_id
    ).order_by(EMI.emi_no).all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ===== TITLE =====
    elements.append(Paragraph("<b>STUDENT PAYMENT REPORT</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.4 * inch))

    # ===== STUDENT INFO CARD =====
    info_data = [
        ["Name", enrollment.name],
        ["Phone", enrollment.phone],
        ["Email", enrollment.email],
        ["Program", enrollment.program],
        ["Payment Type", enrollment.payment_type],
        ["Total Amount", f"₹{enrollment.amount:,.2f}"],
    ]

    info_table = Table(info_data, colWidths=[120, 330])

    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 0.5 * inch))

    # ===== EMI TABLE =====
    table_data = [["EMI", "Amount", "Due Date", "Status", "Paid Date"]]

    for e in emis:
        table_data.append([
            f"#{e.emi_no}",
            f"₹{e.amount:,.2f}",
            e.due_date.strftime("%d-%m-%Y") if e.due_date else "-",
            e.status,
            e.paid_date.strftime("%d-%m-%Y") if e.paid_date else "-"
        ])

    emi_table = Table(table_data, repeatRows=1)

    emi_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        # Borders
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),

        # Alignment
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),

        # Alternate row
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
    ]))

    elements.append(emi_table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{enrollment.name}_Payment_Report.pdf",
        mimetype="application/pdf"
    )


    # ===== STUDENT DETAILS =====
    rows.append("STUDENT DETAILS")
    rows.append("Name,Email,Program,Join Date,Payment Type,Total Amount,Status")
    rows.append(
        f"{enrollment.name},"
        f"{enrollment.email},"
        f"{enrollment.program},"
       f"\"{enrollment.join_date.strftime('%d-%m-%Y') if enrollment.join_date else '-'}\","
        f"{enrollment.payment_type},"
        f"{enrollment.amount},"
        f"{enrollment.status}"
    )

    rows.append("")

    # ===== INSTALLMENT SCHEDULE =====
    rows.append("INSTALLMENT SCHEDULE")
    rows.append("EMI No,Amount,Due Date,Status")

    if emis:
        for e in emis:
            rows.append(
                f"{e.emi_no},"
                f"{e.amount},"
                f"{e.due_date.strftime('%Y-%m-%d') if e.due_date else ''},"
                f"{e.status}"
            )
    else:
        rows.append("No EMI generated yet,,,")

    csv_data = "\n".join(rows)

    response = make_response(csv_data)
    response.headers["Content-Disposition"] = (
        f"attachment; filename=student_{enroll_id}_full_report.csv"
    )
    response.headers["Content-Type"] = "text/csv"

    return response

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file

@app.route("/api/emi/report")
def download_emi_report():
    if not session.get("admin_logged_in"):
        return jsonify(error="Unauthorized"), 401

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ===== TITLE =====
    elements.append(Paragraph("<b>MONTHLY EMI REPORT</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.4 * inch))

    enrollments = Enrollment.query.filter_by(
        payment_type="EMI",
        status="Active"
    ).all()

    for enrollment in enrollments:

        emis = EMI.query.filter_by(
            enrollment_id=enrollment.id
        ).order_by(EMI.emi_no).all()

        # ===== STUDENT INFO CARD =====
        info_data = [
            ["Name", enrollment.name],
            ["Phone", enrollment.phone],
            ["Program", enrollment.program],
            ["Total Amount", f"₹{enrollment.amount:,.2f}"],
        ]

        info_table = Table(info_data, colWidths=[120, 330])

        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))

        # ===== EMI TABLE =====
        table_data = [["EMI", "Amount", "Due Date", "Status", "Paid Date"]]

        for e in emis:
            table_data.append([
                f"#{e.emi_no}",
                f"₹{e.amount:,.2f}",
                e.due_date.strftime("%d-%m-%Y") if e.due_date else "-",
                e.status,
                e.paid_date.strftime("%d-%m-%Y") if e.paid_date else "-"
            ])

        emi_table = Table(table_data, repeatRows=1)

        emi_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),

            # Borders
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),

            # Alignment
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),

            # Alternate rows
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ]))

        elements.append(emi_table)
        elements.append(Spacer(1, 0.6 * inch))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Monthly_EMI_Report.pdf",
        mimetype="application/pdf"
    )




# ================= ROUTES =================

@app.route("/")
def login_page():
    return send_from_directory(PAGES_DIR, "login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/")
    return send_from_directory(PAGES_DIR, "AdminDashboard.html")

@app.route("/pages/<path:f>")
def pages(f):
    return send_from_directory(PAGES_DIR, f)

@app.route("/js/<path:f>")
def js(f):
    return send_from_directory(JS_DIR, f)

@app.route("/css/<path:f>")
def css(f):
    return send_from_directory(CSS_DIR, f)

if __name__ == "__main__":
    app.run(debug=True)
