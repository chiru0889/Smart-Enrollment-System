from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    course_interest = db.Column(db.String(100))
    not_enrolled = db.Column(db.String(50))
    dropout_reason = db.Column(db.Text)
