import io
import csv
import pandas as pd
from datetime import datetime
from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from werkzeug.security import generate_password_hash
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

from app import db
from models import AuditLog, User, StudentProfile


def role_required(role):
    """Decorator to restrict access to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Iltimos, avval tizimga kiring.', 'warning')
                return redirect(url_for('login', next=request.url))
                
            if role == 'admin' and current_user.role != 'admin':
                flash('Sizda bu sahifaga kirish uchun ruxsat yo\'q.', 'danger')
                return redirect(url_for('index'))
                
            if role == 'teacher' and current_user.role not in ['admin', 'teacher']:
                flash('Sizda bu sahifaga kirish uchun ruxsat yo\'q.', 'danger')
                return redirect(url_for('index'))
                
            if role == 'student' and current_user.role not in ['admin', 'student']:
                flash('Sizda bu sahifaga kirish uchun ruxsat yo\'q.', 'danger')
                return redirect(url_for('index'))
                
            if role == 'parent' and current_user.role not in ['admin', 'parent']:
                flash('Sizda bu sahifaga kirish uchun ruxsat yo\'q.', 'danger')
                return redirect(url_for('index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_audit_log(user_id, action, details, ip_address):
    """Create a new audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()
    return log


def generate_pdf_report(df, title):
    """Generate a PDF report from a pandas DataFrame."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    elements.append(Paragraph(title, styles['Title']))
    
    # Add timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"Yaratilgan sana: {timestamp}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal']))  # Spacer
    
    # Convert DataFrame to a list of lists
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Create table
    table = Table(data)
    
    # Add style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    return buffer.getvalue()


def generate_excel_report(df, title):
    """Generate an Excel report from a pandas DataFrame."""
    buffer = BytesIO()
    
    # Create a Pandas Excel writer
    writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
    
    # Convert the DataFrame to an Excel object
    df.to_excel(writer, sheet_name='Report', index=False)
    
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Report']
    
    # Add a header format
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    # Write the column headers with the defined format
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Add title with timestamp
    worksheet.write(0, len(df.columns) + 1, title)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    worksheet.write(1, len(df.columns) + 1, f"Yaratilgan sana: {timestamp}")
    
    # Set column widths
    for i, col in enumerate(df.columns):
        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_len)
    
    # Close the Pandas Excel writer
    writer.close()
    
    return buffer.getvalue()


def process_student_import(file_data):
    """Process student import from CSV data."""
    try:
        # Create CSV reader
        csv_data = csv.reader(io.StringIO(file_data))
        
        # Get header row
        headers = next(csv_data)
        
        # Validate required columns
        required_columns = ['first_name', 'last_name', 'email', 'student_id', 'date_of_birth']
        
        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in headers]
        
        if missing_columns:
            return False, f"Quyidagi ustunlar etishmayapti: {', '.join(missing_columns)}", 0
        
        # Map column indices
        column_indices = {header: idx for idx, header in enumerate(headers)}
        
        # Process data rows
        created_count = 0
        for row in csv_data:
            # Skip empty rows
            if not row or len(row) < len(headers):
                continue
            
            first_name = row[column_indices['first_name']]
            last_name = row[column_indices['last_name']]
            email = row[column_indices['email']]
            student_id = row[column_indices['student_id']]
            date_of_birth = row[column_indices['date_of_birth']]
            
            # Validate required fields
            if not all([first_name, last_name, email, student_id, date_of_birth]):
                continue
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            
            if not existing_user:
                # Generate username
                base_username = f"{first_name.lower()}.{last_name.lower()}"
                username = base_username
                
                # Check if username exists, if so append a number
                suffix = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{suffix}"
                    suffix += 1
                
                # Generate a temporary password (combination of first name and student ID)
                temp_password = f"{first_name.lower()}{student_id[-4:]}"
                
                # Create user
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(temp_password),
                    first_name=first_name,
                    last_name=last_name,
                    role='student',
                    date_registered=datetime.now()
                )
                
                db.session.add(user)
                db.session.flush()  # To get the user ID
                
                # Parse date of birth
                try:
                    # Try different date formats
                    for date_format in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
                        try:
                            dob = datetime.strptime(date_of_birth, date_format).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If none of the formats work
                        dob = None
                except Exception:
                    dob = None
                
                # Create student profile
                profile = StudentProfile(
                    user_id=user.id,
                    student_id=student_id,
                    date_of_birth=dob
                )
                
                db.session.add(profile)
                created_count += 1
        
        # Commit all changes
        db.session.commit()
        
        return True, f"{created_count} ta o'quvchi muvaffaqiyatli import qilindi.", created_count
        
    except Exception as e:
        db.session.rollback()
        return False, f"Import qilishda xatolik yuz berdi: {str(e)}", 0
