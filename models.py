from datetime import datetime
from flask_login import UserMixin
from app import db
from sqlalchemy import ForeignKey, Text


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student, parent
    date_registered = db.Column(db.DateTime, default=datetime.now)
    phone_number = db.Column(db.String(20))
    telegram_id = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    classes_teaching = db.relationship('Class', backref='teacher', lazy=True)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, lazy=True)
    parent_profile = db.relationship('ParentProfile', backref='user', uselist=False, lazy=True)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True)  # School ID or similar
    date_of_birth = db.Column(db.Date)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    parent_connections = db.relationship('ParentStudentConnection', backref='student', lazy=True)
    
    def __repr__(self):
        return f"<StudentProfile {self.user.username}>"


class ParentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relationship = db.Column(db.String(20))  # Mother, father, guardian, etc.
    
    # Relationships
    student_connections = db.relationship('ParentStudentConnection', backref='parent', lazy=True)
    
    def __repr__(self):
        return f"<ParentProfile {self.user.username}>"


class ParentStudentConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_profile_id = db.Column(db.Integer, db.ForeignKey('parent_profile.id'), nullable=False)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    access_token = db.Column(db.String(64), unique=True)  # For parent access links
    
    def __repr__(self):
        return f"<ParentStudentConnection {self.id}>"


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule = db.Column(db.String(120))  # e.g., "Monday, Wednesday 14:00-15:30"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    sessions = db.relationship('ClassSession', backref='class', lazy=True)
    enrollments = db.relationship('Enrollment', backref='class', lazy=True)
    
    def __repr__(self):
        return f"<Class {self.name}>"


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='enrollment', lazy=True)
    comments = db.relationship('StudentComment', backref='enrollment', lazy=True)
    
    def __repr__(self):
        return f"<Enrollment {self.id}>"


class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    topic = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='session', lazy=True)
    
    def __repr__(self):
        return f"<ClassSession {self.date} {self.start_time}>"


class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='present')  # present, absent, late, excused
    recorded_at = db.Column(db.DateTime, default=datetime.now)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)
    
    recorder = db.relationship('User', backref='attendance_records_created')
    
    def __repr__(self):
        return f"<AttendanceRecord {self.id}>"


class StudentComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 scale optional rating
    comment_date = db.Column(db.DateTime, default=datetime.now)
    
    teacher = db.relationship('User', backref='student_comments')
    
    def __repr__(self):
        return f"<StudentComment {self.id}>"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # email, sms, telegram, in-app
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f"<Notification {self.id}>"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    
    def __repr__(self):
        return f"<Message {self.id}>"


class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='password_resets')
    
    def __repr__(self):
        return f"<PasswordReset {self.token}>"


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f"<AuditLog {self.id}>"
