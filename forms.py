from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, SelectField,
    DateField, TextAreaField, TimeField, IntegerField, EmailField,
    FileField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, ValidationError, 
    Regexp, NumberRange
)
from datetime import datetime
from models import User


class LoginForm(FlaskForm):
    username = StringField('Foydalanuvchi nomi', validators=[DataRequired(message="Foydalanuvchi nomini kiriting")])
    password = PasswordField('Parol', validators=[DataRequired(message="Parolni kiriting")])
    remember_me = BooleanField('Meni eslab qol')
    submit = SubmitField('Kirish')


class PasswordResetRequestForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(message="Email manzilini kiriting"), Email(message="To'g'ri email manzilini kiriting")])
    submit = SubmitField('Parolni tiklash')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError("Bu email manzili bilan foydalanuvchi topilmadi")


class PasswordResetForm(FlaskForm):
    password = PasswordField('Yangi parol', validators=[
        DataRequired(message="Yangi parolni kiriting"),
        Length(min=8, message="Parol kamida 8 ta belgidan iborat bo'lishi kerak")
    ])
    confirm_password = PasswordField('Parolni tasdiqlang', validators=[
        DataRequired(message="Parolni qayta kiriting"),
        EqualTo('password', message="Parollar mos kelmadi")
    ])
    submit = SubmitField('Parolni yangilash')


class UserForm(FlaskForm):
    username = StringField('Foydalanuvchi nomi', validators=[
        DataRequired(message="Foydalanuvchi nomini kiriting"),
        Length(min=3, max=64, message="Foydalanuvchi nomi 3-64 ta belgi oralig'ida bo'lishi kerak")
    ])
    email = EmailField('Email', validators=[
        DataRequired(message="Email manzilini kiriting"),
        Email(message="To'g'ri email manzilini kiriting")
    ])
    first_name = StringField('Ism', validators=[DataRequired(message="Ismni kiriting")])
    last_name = StringField('Familiya', validators=[DataRequired(message="Familiyani kiriting")])
    password = PasswordField('Parol', validators=[
        DataRequired(message="Parolni kiriting"),
        Length(min=8, message="Parol kamida 8 ta belgidan iborat bo'lishi kerak")
    ])
    confirm_password = PasswordField('Parolni tasdiqlang', validators=[
        DataRequired(message="Parolni qayta kiriting"),
        EqualTo('password', message="Parollar mos kelmadi")
    ])
    role = SelectField('Rol', choices=[
        ('admin', 'Administrator'),
        ('teacher', 'O\'qituvchi'),
        ('student', 'O\'quvchi'),
        ('parent', 'Ota-ona')
    ], validators=[DataRequired(message="Rolni tanlang")])
    phone_number = StringField('Telefon raqami', validators=[Optional()])
    telegram_id = StringField('Telegram ID', validators=[Optional()])
    submit = SubmitField('Saqlash')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Bu foydalanuvchi nomi allaqachon mavjud")
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Bu email manzili allaqachon ro'yxatdan o'tgan")


class EditUserForm(FlaskForm):
    first_name = StringField('Ism', validators=[DataRequired(message="Ismni kiriting")])
    last_name = StringField('Familiya', validators=[DataRequired(message="Familiyani kiriting")])
    email = EmailField('Email', validators=[
        DataRequired(message="Email manzilini kiriting"),
        Email(message="To'g'ri email manzilini kiriting")
    ])
    role = SelectField('Rol', choices=[
        ('admin', 'Administrator'),
        ('teacher', 'O\'qituvchi'),
        ('student', 'O\'quvchi'),
        ('parent', 'Ota-ona')
    ], validators=[DataRequired(message="Rolni tanlang")])
    phone_number = StringField('Telefon raqami', validators=[Optional()])
    telegram_id = StringField('Telegram ID', validators=[Optional()])
    is_active = BooleanField('Faol')
    submit = SubmitField('Yangilash')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Joriy parol', validators=[DataRequired(message="Joriy parolni kiriting")])
    new_password = PasswordField('Yangi parol', validators=[
        DataRequired(message="Yangi parolni kiriting"),
        Length(min=8, message="Parol kamida 8 ta belgidan iborat bo'lishi kerak")
    ])
    confirm_password = PasswordField('Parolni tasdiqlang', validators=[
        DataRequired(message="Parolni qayta kiriting"),
        EqualTo('new_password', message="Parollar mos kelmadi")
    ])
    submit = SubmitField('Parolni yangilash')


class ClassForm(FlaskForm):
    name = StringField('Sinf nomi', validators=[DataRequired(message="Sinf nomini kiriting")])
    description = TextAreaField('Tavsif', validators=[Optional()])
    teacher_id = SelectField('O\'qituvchi', coerce=int, validators=[DataRequired(message="O'qituvchini tanlang")])
    schedule = StringField('Jadval', validators=[DataRequired(message="Dars jadvalini kiriting")])
    start_date = DateField('Boshlanish sanasi', validators=[DataRequired(message="Boshlanish sanasini kiriting")])
    end_date = DateField('Tugash sanasi', validators=[DataRequired(message="Tugash sanasini kiriting")])
    is_active = BooleanField('Faol', default=True)
    submit = SubmitField('Saqlash')
    
    def validate_end_date(self, end_date):
        if end_date.data < self.start_date.data:
            raise ValidationError("Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak")


class StudentProfileForm(FlaskForm):
    student_id = StringField('O\'quvchi ID', validators=[DataRequired(message="O'quvchi ID raqamini kiriting")])
    date_of_birth = DateField('Tug\'ilgan sana', validators=[DataRequired(message="Tug'ilgan sanani kiriting")])
    submit = SubmitField('Saqlash')


class ParentProfileForm(FlaskForm):
    relationship = SelectField('O\'quvchi bilan bog\'lanish', choices=[
        ('father', 'Otasi'),
        ('mother', 'Onasi'),
        ('guardian', 'Vasiy')
    ], validators=[DataRequired(message="Bog'lanishni tanlang")])
    submit = SubmitField('Saqlash')


class EnrollmentForm(FlaskForm):
    student_id = SelectField('O\'quvchi', coerce=int, validators=[DataRequired(message="O'quvchini tanlang")])
    class_id = SelectField('Sinf', coerce=int, validators=[DataRequired(message="Sinfni tanlang")])
    status = SelectField('Holat', choices=[
        ('active', 'Faol'),
        ('completed', 'Tugatilgan'),
        ('dropped', 'Tark etilgan')
    ], default='active')
    submit = SubmitField('Saqlash')


class ClassSessionForm(FlaskForm):
    date = DateField('Sana', validators=[DataRequired(message="Sanani kiriting")])
    start_time = TimeField('Boshlanish vaqti', validators=[DataRequired(message="Boshlanish vaqtini kiriting")])
    end_time = TimeField('Tugash vaqti', validators=[DataRequired(message="Tugash vaqtini kiriting")])
    topic = StringField('Mavzu', validators=[Optional()])
    notes = TextAreaField('Izohlar', validators=[Optional()])
    submit = SubmitField('Saqlash')
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError("Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak")


class AttendanceForm(FlaskForm):
    session_id = HiddenField('Dars ID')
    submit = SubmitField('Davomatni saqlash')


class AttendanceRecordForm(FlaskForm):
    status = SelectField('Holat', choices=[
        ('present', 'Qatnashdi'),
        ('absent', 'Qatnashmadi'),
        ('late', 'Kechikdi'),
        ('excused', 'Sababli')
    ], default='present')
    notes = TextAreaField('Izohlar', validators=[Optional()])


class StudentCommentForm(FlaskForm):
    comment = TextAreaField('Izoh', validators=[DataRequired(message="Izohni kiriting")])
    rating = SelectField('Baho', choices=[
        ('1', '1 - Juda yomon'),
        ('2', '2 - Yomon'),
        ('3', '3 - O\'rtacha'),
        ('4', '4 - Yaxshi'),
        ('5', '5 - A\'lo')
    ], validators=[Optional()])
    submit = SubmitField('Saqlash')


class MessageForm(FlaskForm):
    recipient_id = SelectField('Qabul qiluvchi', coerce=int, validators=[DataRequired(message="Qabul qiluvchini tanlang")])
    subject = StringField('Mavzu', validators=[DataRequired(message="Xabar mavzusini kiriting")])
    content = TextAreaField('Matn', validators=[DataRequired(message="Xabar matnini kiriting")])
    submit = SubmitField('Yuborish')


class ImportStudentsForm(FlaskForm):
    file = FileField('Excel/CSV fayl', validators=[DataRequired(message="Faylni tanlang")])
    submit = SubmitField('Import qilish')


class ReportFilterForm(FlaskForm):
    class_id = SelectField('Sinf', coerce=int, validators=[Optional()])
    start_date = DateField('Boshlanish sanasi', validators=[Optional()])
    end_date = DateField('Tugash sanasi', validators=[Optional()])
    submit = SubmitField('Hisobotni ko\'rish')
