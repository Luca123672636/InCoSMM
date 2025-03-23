import os
import csv
import io
import uuid
import pandas as pd
from datetime import datetime, timedelta
from flask import (
    render_template, redirect, url_for, flash, request, 
    jsonify, session, abort, send_file
)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc

from app import app, db
from models import (
    User, StudentProfile, ParentProfile, ParentStudentConnection,
    Class, Enrollment, ClassSession, AttendanceRecord, StudentComment,
    Notification, Message, PasswordReset, AuditLog
)
from forms import (
    LoginForm, PasswordResetRequestForm, PasswordResetForm, UserForm,
    EditUserForm, ChangePasswordForm, ClassForm, StudentProfileForm,
    ParentProfileForm, EnrollmentForm, ClassSessionForm, AttendanceForm,
    AttendanceRecordForm, StudentCommentForm, MessageForm, ImportStudentsForm,
    ReportFilterForm
)
from utils import (
    role_required, create_audit_log, generate_pdf_report, 
    generate_excel_report, process_student_import
)


# Basic routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent_dashboard'))
    
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Sizning hisobingiz o\'chirilgan. Administrator bilan bog\'laning.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            create_audit_log(user.id, 'login', 'Tizimga kirish', request.remote_addr)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            flash('Muvaffaqiyatli kirildi!', 'success')
            return redirect(next_page)
        else:
            flash('Noto\'g\'ri foydalanuvchi nomi yoki parol.', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    create_audit_log(current_user.id, 'logout', 'Tizimdan chiqish', request.remote_addr)
    logout_user()
    flash('Siz tizimdan chiqdingiz.', 'info')
    return redirect(url_for('index'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Create reset token
        token = str(uuid.uuid4())
        reset = PasswordReset(user_id=user.id, token=token)
        db.session.add(reset)
        db.session.commit()
        
        # In a real app, send this via email
        reset_url = url_for('reset_password', token=token, _external=True)
        
        flash(f'Parolni tiklash uchun ko\'rsatmalar elektron pochta manzilingizga yuborildi. Reset URL: {reset_url}', 'info')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, title='Parolni Tiklash')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    reset = PasswordReset.query.filter_by(token=token, is_used=False).first()
    if not reset or datetime.now() > reset.created_at + timedelta(hours=24):
        flash('Noto\'g\'ri yoki muddati o\'tgan token.', 'danger')
        return redirect(url_for('reset_password_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.get(reset.user_id)
        user.password_hash = generate_password_hash(form.password.data)
        reset.is_used = True
        db.session.commit()
        
        create_audit_log(user.id, 'password_reset', 'Parol tiklandi', request.remote_addr)
        flash('Parolingiz muvaffaqiyatli yangilandi. Endi yangi parolingiz bilan kirishingiz mumkin.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, title='Yangi Parol')


# Admin routes
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    # Dashboard statistics
    user_stats = {
        'total_users': User.query.count(),
        'total_admins': User.query.filter_by(role='admin').count(),
        'total_teachers': User.query.filter_by(role='teacher').count(),
        'total_students': User.query.filter_by(role='student').count(),
        'total_parents': User.query.filter_by(role='parent').count()
    }
    
    class_stats = {
        'total_classes': Class.query.count(),
        'active_classes': Class.query.filter_by(is_active=True).count()
    }
    
    # Recent activities
    recent_logs = AuditLog.query.order_by(desc(AuditLog.timestamp)).limit(10).all()
    
    # Class attendance summary
    attendance_summary = db.session.query(
        Class.name,
        func.count(AttendanceRecord.id).label('attendance_count'),
        func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_count')
    ).join(ClassSession).join(AttendanceRecord).group_by(Class.id).all()
    
    # Convert to percentage
    attendance_data = []
    for item in attendance_summary:
        if item.attendance_count > 0:
            percentage = (item.present_count / item.attendance_count) * 100
            attendance_data.append({
                'class_name': item.name,
                'percentage': round(percentage, 1)
            })
    
    return render_template(
        'admin/dashboard.html',
        user_stats=user_stats,
        class_stats=class_stats,
        recent_logs=recent_logs,
        attendance_data=attendance_data
    )


@app.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            phone_number=form.phone_number.data,
            telegram_id=form.telegram_id.data,
            date_registered=datetime.now()
        )
        
        db.session.add(user)
        db.session.commit()
        
        # If student, create student profile
        if form.role.data == 'student':
            return redirect(url_for('add_student_profile', user_id=user.id))
        
        # If parent, create parent profile
        if form.role.data == 'parent':
            return redirect(url_for('add_parent_profile', user_id=user.id))
        
        create_audit_log(current_user.id, 'create_user', f'Foydalanuvchi yaratildi: {user.username}', request.remote_addr)
        flash('Foydalanuvchi muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/add_user.html', form=form)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        old_role = user.role
        
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.email = form.email.data
        user.role = form.role.data
        user.phone_number = form.phone_number.data
        user.telegram_id = form.telegram_id.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        
        # If role changed to student and no student profile exists
        if user.role == 'student' and not user.student_profile:
            return redirect(url_for('add_student_profile', user_id=user.id))
        
        # If role changed to parent and no parent profile exists
        if user.role == 'parent' and not user.parent_profile:
            return redirect(url_for('add_parent_profile', user_id=user.id))
        
        create_audit_log(current_user.id, 'update_user', f'Foydalanuvchi yangilandi: {user.username}', request.remote_addr)
        flash('Foydalanuvchi ma\'lumotlari muvaffaqiyatli yangilandi.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('O\'zingizni o\'chira olmaysiz.', 'danger')
        return redirect(url_for('manage_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    create_audit_log(current_user.id, 'delete_user', f'Foydalanuvchi o\'chirildi: {username}', request.remote_addr)
    flash('Foydalanuvchi muvaffaqiyatli o\'chirildi.', 'success')
    return redirect(url_for('manage_users'))


@app.route('/admin/student_profile/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_student_profile(user_id):
    user = User.query.get_or_404(user_id)
    form = StudentProfileForm()
    
    if form.validate_on_submit():
        profile = StudentProfile(
            user_id=user.id,
            student_id=form.student_id.data,
            date_of_birth=form.date_of_birth.data
        )
        
        db.session.add(profile)
        db.session.commit()
        
        create_audit_log(current_user.id, 'create_student_profile', f'O\'quvchi profili yaratildi: {user.username}', request.remote_addr)
        flash('O\'quvchi profili muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/add_student_profile.html', form=form, user=user)


@app.route('/admin/parent_profile/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_parent_profile(user_id):
    user = User.query.get_or_404(user_id)
    form = ParentProfileForm()
    
    if form.validate_on_submit():
        profile = ParentProfile(
            user_id=user.id,
            relationship=form.relationship.data
        )
        
        db.session.add(profile)
        db.session.commit()
        
        create_audit_log(current_user.id, 'create_parent_profile', f'Ota-ona profili yaratildi: {user.username}', request.remote_addr)
        flash('Ota-ona profili muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/add_parent_profile.html', form=form, user=user)


@app.route('/admin/parent_connection/<int:parent_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_parent_connections(parent_id):
    parent = User.query.filter_by(id=parent_id, role='parent').first_or_404()
    parent_profile = parent.parent_profile
    
    if not parent_profile:
        flash('Ota-ona profili yaratilmagan.', 'danger')
        return redirect(url_for('manage_users'))
    
    # Get current connections
    connections = ParentStudentConnection.query.filter_by(parent_profile_id=parent_profile.id).all()
    
    # Get all students
    students = User.query.filter_by(role='student').all()
    
    # For adding new connections
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        
        if student_id:
            student = User.query.filter_by(id=student_id, role='student').first()
            
            if student and student.student_profile:
                # Check if connection already exists
                existing = ParentStudentConnection.query.filter_by(
                    parent_profile_id=parent_profile.id,
                    student_profile_id=student.student_profile.id
                ).first()
                
                if not existing:
                    connection = ParentStudentConnection(
                        parent_profile_id=parent_profile.id,
                        student_profile_id=student.student_profile.id,
                        access_token=str(uuid.uuid4())
                    )
                    
                    db.session.add(connection)
                    db.session.commit()
                    
                    create_audit_log(
                        current_user.id,
                        'create_parent_connection',
                        f'Ota-ona bog\'lanishi yaratildi: {parent.username} -> {student.username}',
                        request.remote_addr
                    )
                    flash('Ota-ona va o\'quvchi bog\'lanishi muvaffaqiyatli yaratildi.', 'success')
                else:
                    flash('Bu bog\'lanish allaqachon mavjud.', 'warning')
            else:
                flash('O\'quvchi topilmadi yoki o\'quvchi profili yaratilmagan.', 'danger')
        
        return redirect(url_for('manage_parent_connections', parent_id=parent_id))
    
    return render_template(
        'admin/manage_parent_connections.html',
        parent=parent,
        connections=connections,
        students=students
    )


@app.route('/admin/parent_connection/delete/<int:connection_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_parent_connection(connection_id):
    connection = ParentStudentConnection.query.get_or_404(connection_id)
    parent_id = connection.parent_profile.user_id
    
    db.session.delete(connection)
    db.session.commit()
    
    create_audit_log(
        current_user.id,
        'delete_parent_connection',
        f'Ota-ona bog\'lanishi o\'chirildi: {connection_id}',
        request.remote_addr
    )
    flash('Ota-ona va o\'quvchi bog\'lanishi muvaffaqiyatli o\'chirildi.', 'success')
    return redirect(url_for('manage_parent_connections', parent_id=parent_id))


@app.route('/admin/classes')
@login_required
@role_required('admin')
def manage_classes():
    classes = Class.query.all()
    return render_template('admin/manage_classes.html', classes=classes)


@app.route('/admin/classes/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_class():
    form = ClassForm()
    
    # Populate teacher choices
    teachers = User.query.filter_by(role='teacher').all()
    form.teacher_id.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in teachers]
    
    if form.validate_on_submit():
        class_obj = Class(
            name=form.name.data,
            description=form.description.data,
            teacher_id=form.teacher_id.data,
            schedule=form.schedule.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data
        )
        
        db.session.add(class_obj)
        db.session.commit()
        
        create_audit_log(current_user.id, 'create_class', f'Sinf yaratildi: {class_obj.name}', request.remote_addr)
        flash('Sinf muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('manage_classes'))
    
    return render_template('admin/add_class.html', form=form)


@app.route('/admin/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    form = ClassForm(obj=class_obj)
    
    # Populate teacher choices
    teachers = User.query.filter_by(role='teacher').all()
    form.teacher_id.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in teachers]
    
    if form.validate_on_submit():
        class_obj.name = form.name.data
        class_obj.description = form.description.data
        class_obj.teacher_id = form.teacher_id.data
        class_obj.schedule = form.schedule.data
        class_obj.start_date = form.start_date.data
        class_obj.end_date = form.end_date.data
        class_obj.is_active = form.is_active.data
        
        db.session.commit()
        
        create_audit_log(current_user.id, 'update_class', f'Sinf yangilandi: {class_obj.name}', request.remote_addr)
        flash('Sinf muvaffaqiyatli yangilandi.', 'success')
        return redirect(url_for('manage_classes'))
    
    return render_template('admin/edit_class.html', form=form, class_obj=class_obj)


@app.route('/admin/classes/delete/<int:class_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    class_name = class_obj.name
    db.session.delete(class_obj)
    db.session.commit()
    
    create_audit_log(current_user.id, 'delete_class', f'Sinf o\'chirildi: {class_name}', request.remote_addr)
    flash('Sinf muvaffaqiyatli o\'chirildi.', 'success')
    return redirect(url_for('manage_classes'))


@app.route('/admin/enrollments/<int:class_id>')
@login_required
@role_required('admin')
def manage_enrollments(class_id):
    class_obj = Class.query.get_or_404(class_id)
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    
    return render_template(
        'admin/manage_enrollments.html',
        class_obj=class_obj,
        enrollments=enrollments
    )


@app.route('/admin/enrollments/add/<int:class_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_enrollment(class_id):
    class_obj = Class.query.get_or_404(class_id)
    form = EnrollmentForm()
    
    # Get all students with profiles
    students = User.query.filter_by(role='student').all()
    student_choices = []
    
    for student in students:
        if student.student_profile:
            # Check if student is not already enrolled
            enrollment = Enrollment.query.filter_by(
                student_profile_id=student.student_profile.id,
                class_id=class_id
            ).first()
            
            if not enrollment:
                student_choices.append((student.student_profile.id, f"{student.first_name} {student.last_name}"))
    
    form.student_id.choices = student_choices
    form.class_id.data = class_id
    
    if form.validate_on_submit():
        enrollment = Enrollment(
            student_profile_id=form.student_id.data,
            class_id=class_id,
            status=form.status.data
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        create_audit_log(
            current_user.id,
            'create_enrollment',
            f'O\'quvchi sinfga qo\'shildi: {enrollment.student.user.username} -> {class_obj.name}',
            request.remote_addr
        )
        flash('O\'quvchi sinfga muvaffaqiyatli qo\'shildi.', 'success')
        return redirect(url_for('manage_enrollments', class_id=class_id))
    
    return render_template(
        'admin/add_enrollment.html',
        form=form,
        class_obj=class_obj
    )


@app.route('/admin/enrollments/delete/<int:enrollment_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    class_id = enrollment.class_id
    
    db.session.delete(enrollment)
    db.session.commit()
    
    # Get class and student info
    class_obj = Class.query.get(enrollment.class_id)
    class_name = class_obj.name if class_obj else "N/A"
    student_name = enrollment.student.user.username if enrollment.student and enrollment.student.user else "N/A"
    create_audit_log(
        current_user.id,
        'delete_enrollment',
        f"O'quvchi sinfdan o'chirildi: {student_name} -> {class_name}",
        request.remote_addr
    )
    flash('O\'quvchi sinfdan muvaffaqiyatli o\'chirildi.', 'success')
    return redirect(url_for('manage_enrollments', class_id=class_id))


@app.route('/admin/sessions/<int:class_id>')
@login_required
@role_required('admin')
def manage_sessions(class_id):
    class_obj = Class.query.get_or_404(class_id)
    sessions = ClassSession.query.filter_by(class_id=class_id).order_by(ClassSession.date.desc()).all()
    
    return render_template(
        'admin/manage_sessions.html',
        class_obj=class_obj,
        sessions=sessions
    )


@app.route('/admin/sessions/add/<int:class_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_session(class_id):
    class_obj = Class.query.get_or_404(class_id)
    form = ClassSessionForm()
    
    if form.validate_on_submit():
        session = ClassSession(
            class_id=class_id,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            topic=form.topic.data,
            notes=form.notes.data
        )
        
        db.session.add(session)
        db.session.commit()
        
        create_audit_log(
            current_user.id,
            'create_session',
            f'Dars yaratildi: {class_obj.name} {form.date.data}',
            request.remote_addr
        )
        flash('Dars muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('manage_sessions', class_id=class_id))
    
    return render_template(
        'admin/add_session.html',
        form=form,
        class_obj=class_obj
    )


@app.route('/admin/reports')
@login_required
@role_required('admin')
def reports():
    form = ReportFilterForm()
    
    # Populate class choices
    classes = Class.query.all()
    form.class_id.choices = [(0, 'Barcha sinflar')] + [(c.id, c.name) for c in classes]
    
    return render_template('admin/reports.html', form=form)


@app.route('/admin/reports/attendance', methods=['POST'])
@login_required
@role_required('admin')
def attendance_report():
    form = ReportFilterForm()
    
    # Populate class choices
    classes = Class.query.all()
    form.class_id.choices = [(0, 'Barcha sinflar')] + [(c.id, c.name) for c in classes]
    
    if form.validate_on_submit():
        class_id = form.class_id.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        # Generate report data
        query = db.session.query(
            User.first_name,
            User.last_name,
            Class.name.label('class_name'),
            ClassSession.date,
            AttendanceRecord.status
        ).join(
            StudentProfile, User.id == StudentProfile.user_id
        ).join(
            Enrollment, StudentProfile.id == Enrollment.student_profile_id
        ).join(
            Class, Enrollment.class_id == Class.id
        ).join(
            ClassSession, Class.id == ClassSession.class_id
        ).join(
            AttendanceRecord, (Enrollment.id == AttendanceRecord.enrollment_id) & 
                             (ClassSession.id == AttendanceRecord.session_id)
        )
        
        # Apply filters
        if class_id != 0:
            query = query.filter(Class.id == class_id)
        
        if start_date:
            query = query.filter(ClassSession.date >= start_date)
        
        if end_date:
            query = query.filter(ClassSession.date <= end_date)
        
        results = query.order_by(User.last_name, User.first_name, ClassSession.date).all()
        
        # Convert to DataFrame for easier processing
        data = []
        for result in results:
            status_text = {
                'present': 'Qatnashdi',
                'absent': 'Qatnashmadi',
                'late': 'Kechikdi',
                'excused': 'Sababli'
            }.get(result.status, result.status)
            
            data.append({
                'Ism': result.first_name,
                'Familiya': result.last_name,
                'Sinf': result.class_name,
                'Sana': result.date.strftime('%Y-%m-%d'),
                'Holat': status_text
            })
        
        df = pd.DataFrame(data)
        
        # Generate report based on requested format
        format_type = request.form.get('format', 'html')
        
        if format_type == 'pdf':
            pdf_bytes = generate_pdf_report(df, 'Davomat hisoboti')
            
            # Create in-memory file
            pdf_io = io.BytesIO(pdf_bytes)
            pdf_io.seek(0)
            
            create_audit_log(current_user.id, 'generate_report', 'PDF davomat hisoboti yaratildi', request.remote_addr)
            return send_file(
                pdf_io,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='davomat_hisoboti.pdf'
            )
        
        elif format_type == 'excel':
            excel_bytes = generate_excel_report(df, 'Davomat hisoboti')
            
            # Create in-memory file
            excel_io = io.BytesIO(excel_bytes)
            excel_io.seek(0)
            
            create_audit_log(current_user.id, 'generate_report', 'Excel davomat hisoboti yaratildi', request.remote_addr)
            return send_file(
                excel_io,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='davomat_hisoboti.xlsx'
            )
        
        else:  # HTML format
            return render_template(
                'admin/report_results.html',
                data=data,
                report_type='Davomat hisoboti'
            )
    
    flash('Hisobot yaratishda xatolik yuz berdi.', 'danger')
    return redirect(url_for('reports'))


@app.route('/admin/import_students', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def import_students():
    form = ImportStudentsForm()
    
    if form.validate_on_submit():
        # Get file data
        file_data = request.files['file'].read().decode('utf-8')
        
        # Process the data
        success, message, created_count = process_student_import(file_data)
        
        if success:
            create_audit_log(current_user.id, 'import_students', f'{created_count} ta o\'quvchi import qilindi', request.remote_addr)
            flash(message, 'success')
            return redirect(url_for('manage_users'))
        else:
            flash(message, 'danger')
    
    return render_template('admin/import_students.html', form=form)


# Teacher routes
@app.route('/teacher/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    # Get classes taught by this teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    # Get recent sessions
    recent_sessions = db.session.query(ClassSession, Class).join(
        Class, ClassSession.class_id == Class.id
    ).filter(
        Class.teacher_id == current_user.id
    ).order_by(
        ClassSession.date.desc()
    ).limit(5).all()
    
    # Calculate attendance statistics
    class_stats = []
    for class_obj in classes:
        total_sessions = ClassSession.query.filter_by(class_id=class_obj.id).count()
        enrollments = Enrollment.query.filter_by(class_id=class_obj.id).count()
        
        if total_sessions > 0 and enrollments > 0:
            attendance_records = db.session.query(AttendanceRecord).join(
                ClassSession, AttendanceRecord.session_id == ClassSession.id
            ).filter(
                ClassSession.class_id == class_obj.id
            ).count()
            
            present_records = db.session.query(AttendanceRecord).join(
                ClassSession, AttendanceRecord.session_id == ClassSession.id
            ).filter(
                ClassSession.class_id == class_obj.id,
                AttendanceRecord.status == 'present'
            ).count()
            
            if attendance_records > 0:
                attendance_rate = (present_records / attendance_records) * 100
            else:
                attendance_rate = 0
            
            class_stats.append({
                'class': class_obj,
                'total_sessions': total_sessions,
                'enrollments': enrollments,
                'attendance_rate': round(attendance_rate, 1)
            })
    
    return render_template(
        'teacher/dashboard.html',
        classes=classes,
        recent_sessions=recent_sessions,
        class_stats=class_stats
    )


@app.route('/teacher/classes')
@login_required
@role_required('teacher')
def teacher_classes():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/classes.html', classes=classes)


@app.route('/teacher/class/<int:class_id>')
@login_required
@role_required('teacher')
def teacher_class_detail(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify this teacher is assigned to this class
    if class_obj.teacher_id != current_user.id:
        flash('Sizda bu sinfga kirish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    # Get enrolled students
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    
    # Get recent sessions
    sessions = ClassSession.query.filter_by(class_id=class_id).order_by(ClassSession.date.desc()).limit(10).all()
    
    return render_template(
        'teacher/class_detail.html',
        class_obj=class_obj,
        enrollments=enrollments,
        sessions=sessions
    )


@app.route('/teacher/attendance/<int:class_id>')
@login_required
@role_required('teacher')
def teacher_attendance(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify this teacher is assigned to this class
    if class_obj.teacher_id != current_user.id:
        flash('Sizda bu sinfga kirish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    # Get enrolled students
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    
    # Get sessions for this class
    sessions = ClassSession.query.filter_by(class_id=class_id).order_by(ClassSession.date.desc()).all()
    
    # Get attendance records for visualization
    attendance_data = {}
    
    for enrollment in enrollments:
        student_name = f"{enrollment.student.user.first_name} {enrollment.student.user.last_name}"
        attendance_data[student_name] = {
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0
        }
        
        # Count attendance by status
        records = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
        for record in records:
            attendance_data[student_name][record.status] += 1
    
    return render_template(
        'teacher/attendance.html',
        class_obj=class_obj,
        enrollments=enrollments,
        sessions=sessions,
        attendance_data=attendance_data
    )


@app.route('/teacher/mark_attendance/<int:session_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def mark_attendance(session_id):
    session = ClassSession.query.get_or_404(session_id)
    class_obj = Class.query.get(session.class_id)
    
    # Verify this teacher is assigned to this class
    if class_obj.teacher_id != current_user.id:
        flash('Sizda bu sinfga kirish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    # Get enrolled students
    enrollments = Enrollment.query.filter_by(class_id=class_obj.id).all()
    
    # Create main form and individual record forms
    form = AttendanceForm()
    record_forms = {}
    
    for enrollment in enrollments:
        # Check if attendance record already exists
        record = AttendanceRecord.query.filter_by(
            enrollment_id=enrollment.id,
            session_id=session_id
        ).first()
        
        # Create a form for this student
        record_form = AttendanceRecordForm(prefix=f"student_{enrollment.id}")
        
        if record:
            # Pre-populate form with existing data
            record_form.status.data = record.status
            record_form.notes.data = record.notes
        
        record_forms[enrollment.id] = record_form
    
    if form.validate_on_submit():
        for enrollment in enrollments:
            record_form = record_forms[enrollment.id]
            
            # Check if attendance record already exists
            record = AttendanceRecord.query.filter_by(
                enrollment_id=enrollment.id,
                session_id=session_id
            ).first()
            
            if record:
                # Update existing record
                record.status = request.form.get(f"student_{enrollment.id}-status")
                record.notes = request.form.get(f"student_{enrollment.id}-notes")
                record.recorded_at = datetime.now()
                record.recorded_by = current_user.id
            else:
                # Create new record
                record = AttendanceRecord(
                    enrollment_id=enrollment.id,
                    session_id=session_id,
                    status=request.form.get(f"student_{enrollment.id}-status"),
                    notes=request.form.get(f"student_{enrollment.id}-notes"),
                    recorded_by=current_user.id
                )
                db.session.add(record)
        
        db.session.commit()
        
        create_audit_log(
            current_user.id,
            'mark_attendance',
            f'Davomat belgilandi: {class_obj.name}, {session.date}',
            request.remote_addr
        )
        flash('Davomat muvaffaqiyatli saqlandi.', 'success')
        return redirect(url_for('teacher_attendance', class_id=class_obj.id))
    
    return render_template(
        'teacher/mark_attendance.html',
        form=form,
        record_forms=record_forms,
        session=session,
        class_obj=class_obj,
        enrollments=enrollments
    )


@app.route('/teacher/comments/<int:enrollment_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def student_comments(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    class_obj = Class.query.get(enrollment.class_id)
    student = enrollment.student.user
    
    # Verify this teacher is assigned to this class
    if class_obj.teacher_id != current_user.id:
        flash('Sizda bu o\'quvchiga izoh qoldirish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    # Get existing comments
    comments = StudentComment.query.filter_by(enrollment_id=enrollment_id).order_by(StudentComment.comment_date.desc()).all()
    
    # Create form for new comment
    form = StudentCommentForm()
    
    if form.validate_on_submit():
        comment = StudentComment(
            enrollment_id=enrollment_id,
            teacher_id=current_user.id,
            comment=form.comment.data,
            rating=form.rating.data if form.rating.data else None
        )
        
        db.session.add(comment)
        db.session.commit()
        
        create_audit_log(
            current_user.id,
            'add_comment',
            f'O\'quvchiga izoh qoldirildi: {student.first_name} {student.last_name}',
            request.remote_addr
        )
        flash('Izoh muvaffaqiyatli qo\'shildi.', 'success')
        return redirect(url_for('student_comments', enrollment_id=enrollment_id))
    
    return render_template(
        'teacher/student_comments.html',
        form=form,
        enrollment=enrollment,
        class_obj=class_obj,
        student=student,
        comments=comments
    )


@app.route('/teacher/sessions/add/<int:class_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_add_session(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify this teacher is assigned to this class
    if class_obj.teacher_id != current_user.id:
        flash('Sizda bu sinfga dars qo\'shish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('teacher_classes'))
    
    form = ClassSessionForm()
    
    if form.validate_on_submit():
        session = ClassSession(
            class_id=class_id,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            topic=form.topic.data,
            notes=form.notes.data
        )
        
        db.session.add(session)
        db.session.commit()
        
        create_audit_log(
            current_user.id,
            'create_session',
            f'Dars yaratildi: {class_obj.name} {form.date.data}',
            request.remote_addr
        )
        flash('Dars muvaffaqiyatli yaratildi.', 'success')
        return redirect(url_for('teacher_class_detail', class_id=class_id))
    
    return render_template(
        'teacher/add_session.html',
        form=form,
        class_obj=class_obj
    )


# Student routes
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    # Get student profile
    student_profile = current_user.student_profile
    
    if not student_profile:
        flash('Sizning o\'quvchi profilingiz topilmadi.', 'danger')
        return redirect(url_for('index'))
    
    # Get classes enrolled in
    enrollments = Enrollment.query.filter_by(student_profile_id=student_profile.id).all()
    
    # Calculate attendance statistics
    attendance_stats = []
    perfect_attendance = True
    
    for enrollment in enrollments:
        class_obj = enrollment.class_
        
        attendance_records = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
        total_records = len(attendance_records)
        
        if total_records > 0:
            present_count = sum(1 for record in attendance_records if record.status == 'present')
            absent_count = sum(1 for record in attendance_records if record.status == 'absent')
            late_count = sum(1 for record in attendance_records if record.status == 'late')
            excused_count = sum(1 for record in attendance_records if record.status == 'excused')
            
            attendance_rate = (present_count / total_records) * 100
            
            if absent_count > 0 or late_count > 0:
                perfect_attendance = False
            
            attendance_stats.append({
                'class': class_obj,
                'attendance_rate': round(attendance_rate, 1),
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'excused_count': excused_count,
                'total_sessions': total_records
            })
    
    # Get recent comments from teachers
    comments = db.session.query(StudentComment, Class).join(
        Enrollment, StudentComment.enrollment_id == Enrollment.id
    ).join(
        Class, Enrollment.class_id == Class.id
    ).filter(
        Enrollment.student_profile_id == student_profile.id
    ).order_by(
        StudentComment.comment_date.desc()
    ).limit(5).all()
    
    return render_template(
        'student/dashboard.html',
        student_profile=student_profile,
        enrollments=enrollments,
        attendance_stats=attendance_stats,
        perfect_attendance=perfect_attendance,
        comments=comments
    )


@app.route('/student/attendance')
@login_required
@role_required('student')
def student_attendance():
    # Get student profile
    student_profile = current_user.student_profile
    
    if not student_profile:
        flash('Sizning o\'quvchi profilingiz topilmadi.', 'danger')
        return redirect(url_for('index'))
    
    # Get classes enrolled in
    enrollments = Enrollment.query.filter_by(student_profile_id=student_profile.id).all()
    
    # Get attendance records for each class
    class_attendance = {}
    
    for enrollment in enrollments:
        class_obj = enrollment.class_
        
        # Get attendance records for this enrollment
        records = db.session.query(AttendanceRecord, ClassSession).join(
            ClassSession, AttendanceRecord.session_id == ClassSession.id
        ).filter(
            AttendanceRecord.enrollment_id == enrollment.id
        ).order_by(
            ClassSession.date.desc()
        ).all()
        
        class_attendance[class_obj.id] = {
            'class': class_obj,
            'records': records
        }
    
    return render_template(
        'student/attendance_history.html',
        student_profile=student_profile,
        class_attendance=class_attendance
    )


# Parent routes
@app.route('/parent/dashboard')
@login_required
@role_required('parent')
def parent_dashboard():
    # Get parent profile
    parent_profile = current_user.parent_profile
    
    if not parent_profile:
        flash('Sizning ota-ona profilingiz topilmadi.', 'danger')
        return redirect(url_for('index'))
    
    # Get connected students
    connections = ParentStudentConnection.query.filter_by(parent_profile_id=parent_profile.id).all()
    
    # Get information for each connected student
    student_data = []
    
    for connection in connections:
        student_profile = connection.student
        student = student_profile.user
        
        # Get enrollments
        enrollments = Enrollment.query.filter_by(student_profile_id=student_profile.id).all()
        
        # Get attendance summary
        attendance_summary = []
        
        for enrollment in enrollments:
            class_obj = enrollment.class_
            
            records = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
            total_records = len(records)
            
            if total_records > 0:
                present_count = sum(1 for record in records if record.status == 'present')
                absent_count = sum(1 for record in records if record.status == 'absent')
                late_count = sum(1 for record in records if record.status == 'late')
                excused_count = sum(1 for record in records if record.status == 'excused')
                
                attendance_rate = (present_count / total_records) * 100
                
                attendance_summary.append({
                    'class': class_obj,
                    'attendance_rate': round(attendance_rate, 1),
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'excused_count': excused_count,
                    'total_sessions': total_records
                })
        
        # Get recent comments
        comments = db.session.query(StudentComment, Class, User).join(
            Enrollment, StudentComment.enrollment_id == Enrollment.id
        ).join(
            Class, Enrollment.class_id == Class.id
        ).join(
            User, StudentComment.teacher_id == User.id
        ).filter(
            Enrollment.student_profile_id == student_profile.id
        ).order_by(
            StudentComment.comment_date.desc()
        ).limit(3).all()
        
        student_data.append({
            'student': student,
            'enrollments': enrollments,
            'attendance_summary': attendance_summary,
            'comments': comments
        })
    
    return render_template(
        'parent/dashboard.html',
        parent_profile=parent_profile,
        student_data=student_data
    )


@app.route('/parent/student/<int:student_id>')
@login_required
@role_required('parent')
def parent_student_view(student_id):
    # Get parent profile
    parent_profile = current_user.parent_profile
    
    if not parent_profile:
        flash('Sizning ota-ona profilingiz topilmadi.', 'danger')
        return redirect(url_for('index'))
    
    # Verify connection to student
    student = User.query.get_or_404(student_id)
    
    if not student.student_profile:
        flash('O\'quvchi profili topilmadi.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    connection = ParentStudentConnection.query.filter_by(
        parent_profile_id=parent_profile.id,
        student_profile_id=student.student_profile.id
    ).first()
    
    if not connection:
        flash('Sizda bu o\'quvchini ko\'rish uchun ruxsat yo\'q.', 'danger')
        return redirect(url_for('parent_dashboard'))
    
    # Get enrollments
    enrollments = Enrollment.query.filter_by(student_profile_id=student.student_profile.id).all()
    
    # Get attendance records for each class
    class_attendance = {}
    
    for enrollment in enrollments:
        class_obj = enrollment.class_
        
        # Get attendance records for this enrollment
        records = db.session.query(AttendanceRecord, ClassSession).join(
            ClassSession, AttendanceRecord.session_id == ClassSession.id
        ).filter(
            AttendanceRecord.enrollment_id == enrollment.id
        ).order_by(
            ClassSession.date.desc()
        ).all()
        
        class_attendance[class_obj.id] = {
            'class': class_obj,
            'records': records
        }
    
    # Get all comments from teachers
    comments = db.session.query(StudentComment, Class, User).join(
        Enrollment, StudentComment.enrollment_id == Enrollment.id
    ).join(
        Class, Enrollment.class_id == Class.id
    ).join(
        User, StudentComment.teacher_id == User.id
    ).filter(
        Enrollment.student_profile_id == student.student_profile.id
    ).order_by(
        StudentComment.comment_date.desc()
    ).all()
    
    return render_template(
        'parent/student_view.html',
        student=student,
        enrollments=enrollments,
        class_attendance=class_attendance,
        comments=comments
    )


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# API routes for AJAX
@app.route('/api/attendance_stats/<int:class_id>')
@login_required
def api_attendance_stats(class_id):
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    class_obj = Class.query.get_or_404(class_id)
    
    # Verify permission
    if current_user.role == 'teacher' and class_obj.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get enrollments
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    
    # Calculate attendance for each student
    student_data = []
    labels = []
    present_data = []
    absent_data = []
    late_data = []
    
    for enrollment in enrollments:
        student = enrollment.student.user
        labels.append(f"{student.first_name} {student.last_name}")
        
        attendance = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
        
        present_count = sum(1 for record in attendance if record.status == 'present')
        absent_count = sum(1 for record in attendance if record.status == 'absent')
        late_count = sum(1 for record in attendance if record.status == 'late')
        excused_count = sum(1 for record in attendance if record.status == 'excused')
        
        total_count = len(attendance)
        
        if total_count > 0:
            present_percent = (present_count / total_count) * 100
            absent_percent = (absent_count / total_count) * 100
            late_percent = (late_count / total_count) * 100
        else:
            present_percent = absent_percent = late_percent = 0
        
        present_data.append(round(present_percent, 1))
        absent_data.append(round(absent_percent, 1))
        late_data.append(round(late_percent, 1))
        
        student_data.append({
            'name': f"{student.first_name} {student.last_name}",
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'excused': excused_count,
            'total': total_count,
            'present_percent': round(present_percent, 1)
        })
    
    return jsonify({
        'student_data': student_data,
        'chart_data': {
            'labels': labels,
            'present_data': present_data,
            'absent_data': absent_data,
            'late_data': late_data
        }
    })


@app.route('/api/student_attendance/<int:student_id>')
@login_required
def api_student_attendance(student_id):
    student = User.query.get_or_404(student_id)
    
    if not student.student_profile:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # Verify permission
    if current_user.role == 'student' and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if current_user.role == 'parent':
        parent_profile = current_user.parent_profile
        if not parent_profile:
            return jsonify({'error': 'Parent profile not found'}), 404
        
        connection = ParentStudentConnection.query.filter_by(
            parent_profile_id=parent_profile.id,
            student_profile_id=student.student_profile.id
        ).first()
        
        if not connection:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Get enrollments
    enrollments = Enrollment.query.filter_by(student_profile_id=student.student_profile.id).all()
    
    # Get attendance data for each class
    class_data = []
    
    for enrollment in enrollments:
        class_obj = enrollment.class_
        
        attendance = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
        
        present_count = sum(1 for record in attendance if record.status == 'present')
        absent_count = sum(1 for record in attendance if record.status == 'absent')
        late_count = sum(1 for record in attendance if record.status == 'late')
        excused_count = sum(1 for record in attendance if record.status == 'excused')
        
        total_count = len(attendance)
        
        class_data.append({
            'class_name': class_obj.name,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'excused': excused_count,
            'total': total_count
        })
    
    # Prepare data for chart
    chart_data = {
        'labels': [data['class_name'] for data in class_data],
        'present': [data['present'] for data in class_data],
        'absent': [data['absent'] for data in class_data],
        'late': [data['late'] for data in class_data],
        'excused': [data['excused'] for data in class_data]
    }
    
    return jsonify({
        'class_data': class_data,
        'chart_data': chart_data
    })
