from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import pytz
from celery import Celery
from celery.schedules import crontab
import redis
import csv
import io
import json
import os
import logging

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

# CORS configuration
CORS(app, supports_credentials=True, origins=["http://localhost:8080"])

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'parking.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Redis configuration
app.config["REDIS_URL"] = "redis://localhost:6379/0"

# Email configuration (Gmail SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pahariyascafe@gmail.com'  
app.config['MAIL_PASSWORD'] = 'wxim bfnj bbhv makx'     
app.config['MAIL_DEFAULT_SENDER'] = 'pahariyascafe@gmail.com'

# Celery configuration
app.config.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=False,  
)

#using ist timezone not utc
IST = pytz.timezone('Asia/Kolkata')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('result_backend'), 
        broker=app.config.get('broker_url')       
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=False,  
        beat_schedule={
            'send-daily-reminders': {
                'task': 'app.send_daily_reminders',
                'schedule': 60.0,
            },
            'send-monthly-reports': {
                'task': 'app.send_monthly_reports',
                'schedule': 300.0,
            },
        }
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


celery = make_celery(app)


# Models 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)  # Track last activity
    
    reservations = db.relationship("ReserveParkingSpot", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'pin_code': self.pin_code,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    number_of_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', cascade="all, delete-orphan")

    def to_dict(self):
        available_spots = sum(1 for spot in self.parking_spots if spot.status == 'A')
        occupied_spots = self.number_of_spots - available_spots
        
        return {
            'id': self.id,
            'prime_location_name': self.prime_location_name,
            'price': self.price,
            'address': self.address,
            'pin_code': self.pin_code,
            'number_of_spots': self.number_of_spots,
            'available_spots': available_spots,
            'occupied_spots': occupied_spots,
            'spots': [spot.to_dict() for spot in self.parking_spots],
            'created_at': self.created_at.isoformat()
        }

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  # A: Available, O: Occupied
    
    reservations = db.relationship('ReserveParkingSpot', backref='parking_spot', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'lot_id': self.lot_id,
            'spot_number': self.spot_number,
            'status': self.status
        }

class ReserveParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(10), default='active')  # active, completed
    remarks = db.Column(db.String(500), nullable=True)  # For CSV export
    
    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'user_id': self.user_id,
            'vehicle_number': self.vehicle_number,
            'parking_timestamp': self.parking_timestamp.isoformat(),
            'leaving_timestamp': self.leaving_timestamp.isoformat() if self.leaving_timestamp else None,
            'parking_cost': self.parking_cost,
            'status': self.status,
            'remarks': self.remarks,
            'parking_lot': self.parking_spot.parking_lot.prime_location_name,
            'spot_number': self.parking_spot.spot_number
        }

class ExportJob(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # Celery task ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)  # 'csv_export', 'monthly_report'
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    
    user = db.relationship('User', backref='export_jobs')

# Cache management functions
def get_cache(key):
    """Get data from Redis cache"""
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logging.error(f"Cache get error: {e}")
    return None

def set_cache(key, value, timeout=300):
    """Set data in Redis cache with expiry"""
    try:
        redis_client.setex(key, timeout, json.dumps(value))
    except Exception as e:
        logging.error(f"Cache set error: {e}")

def delete_cache(*keys):
    """Delete cache keys"""
    try:
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logging.error(f"Cache delete error: {e}")

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('is_admin', False)

def get_current_user():
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

def update_user_activity(user_id):
    """Update user's last login time"""
    try:
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        logging.error(f"Error updating user activity: {e}")

def get_current_time():
    """Get current time in IST timezone"""
    return datetime.now(IST)


def format_time_display(dt):
    """Format datetime for consistent display"""
    if dt:
        return dt.strftime('%d/%m/%Y, %I:%M:%S %p')
    return 'N/A'

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'full_name', 'phone', 'address', 'pin_code']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        user = User(
            email=data['email'],
            full_name=data['full_name'],
            phone=data['phone'],
            address=data['address'],
            pin_code=data['pin_code']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            
            # Update last login
            update_user_activity(user.id)
            
            # Clear user-specific caches
            delete_cache(f"user_dashboard_stats_{user.id}", f"user_reservations_{user.id}")
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    if is_logged_in():
        user_id = session['user_id']
        delete_cache(f"user_dashboard_stats_{user_id}", f"user_reservations_{user_id}")
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/me', methods=['GET'])
def get_current_user_info():
    if not is_logged_in():
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_current_user()
    return jsonify({'user': user.to_dict()}), 200

# Enhanced Admin Routes with Caching
@app.route('/api/admin/parking-lots', methods=['GET'])
def get_all_parking_lots():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    cache_key = "admin_parking_lots"
    cached_data = get_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data), 200
    
    lots = ParkingLot.query.all()
    lots_data = [lot.to_dict() for lot in lots]
    
    # Cache for 5 minutes
    set_cache(cache_key, lots_data, 300)
    
    return jsonify(lots_data), 200

@app.route('/api/admin/parking-lots', methods=['POST'])
def create_parking_lot():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        
        required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'number_of_spots']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        parking_lot = ParkingLot(
            prime_location_name=data['prime_location_name'],
            price=float(data['price']),
            address=data['address'],
            pin_code=data['pin_code'],
            number_of_spots=int(data['number_of_spots'])
        )
        
        db.session.add(parking_lot)
        db.session.commit()
        
        # Create parking spots
        for i in range(1, int(data['number_of_spots']) + 1):
            spot = ParkingSpot(
                lot_id=parking_lot.id,
                spot_number=i,
                status='A'
            )
            db.session.add(spot)
        
        db.session.commit()
        
        # Clear related caches
        delete_cache("admin_parking_lots", "user_parking_lots", "admin_dashboard_stats")
        
        return jsonify({'message': 'Parking lot created successfully', 'lot': parking_lot.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Celery Tasks
@celery.task(name='app.send_daily_reminders')
def send_daily_reminders():
    """Send daily reminders to inactive users"""
    with app.app_context():
        try:
            # Get users who haven't logged in for the last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            inactive_users = db.session.query(User).filter(
                User.is_admin == False,
                db.or_(
                    User.last_login < week_ago,
                    User.last_login == None
                )
            ).all()
            
            # Get available parking lots
            available_lots = db.session.query(ParkingLot).join(ParkingSpot).filter(
                ParkingSpot.status == 'A'
            ).distinct().limit(5).all()
            
            sent_count = 0
            for user in inactive_users:
                try:
                    # reminder email content
                    subject = "UrbanPark - Daily Parking Reminder"
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; }}
                            .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .content {{ padding: 20px; }}
                            .lot-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                            .btn {{ background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>UrbanPark Daily Reminder</h1>
                            </div>
                            <div class="content">
                                <h2>Hi {user.full_name},</h2>
                                <p>We noticed you haven't used UrbanPark recently. Don't miss out on convenient parking spots!</p>
                                
                                <h3>🅿️ Available Parking Spots Today:</h3>
                                {''.join([f'''
                                <div class="lot-item">
                                    <strong>{lot.prime_location_name}</strong><br>
                                    <small>{lot.address}</small><br>
                                    <span style="color: #28a745; font-weight: bold;">₹{lot.price}/hour</span>
                                </div>
                                ''' for lot in available_lots])}
                                
                                <p style="text-align: center; margin-top: 30px;">
                                    <a href="http://localhost:8080/parking-lots" class="btn">Book Parking Now</a>
                                </p>
                                
                                <hr style="margin: 30px 0;">
                                <p style="font-size: 12px; color: #666; text-align: center;">
                                    This is an automated reminder. You can manage your preferences in your dashboard.
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Send email
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        html=html_content
                    )
                    mail.send(msg)
                    sent_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to send reminder to {user.email}: {e}")
                    continue
            
            return f"Daily reminders sent to {sent_count} users"
            
        except Exception as e:
            logging.error(f"Daily reminder task failed: {e}")
            return f"Daily reminder task failed: {str(e)}"

@celery.task(name='app.send_monthly_reports')
def send_monthly_reports():
    """Send monthly activity reports to all users"""
    with app.app_context():
        try:
            now = datetime.utcnow()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
            
            users = db.session.query(User).filter(User.is_admin == False).all()
            sent_count = 0
            
            for user in users:
                try:
                    # Get user's bookings for last month
                    reservations = db.session.query(ReserveParkingSpot).filter(
                        ReserveParkingSpot.user_id == user.id,
                        ReserveParkingSpot.parking_timestamp >= start_of_last_month,
                        ReserveParkingSpot.parking_timestamp < start_of_month
                    ).all()
                    
                    if not reservations:
                        continue  # Skip users with no activity
                    
                    # Calculate statistics
                    total_bookings = len(reservations)
                    total_spent = sum(r.parking_cost or 0 for r in reservations)
                    completed_bookings = len([r for r in reservations if r.status == 'completed'])
                    
                    # Find most used parking lot
                    lot_usage = {}
                    for r in reservations:
                        lot_name = r.parking_spot.parking_lot.prime_location_name
                        lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
                    most_used_lot = max(lot_usage.items(), key=lambda x: x[1])[0] if lot_usage else "None"
                    
                    # monthly parking report
                    subject = f"🅿️ Your Monthly Parking Report - {start_of_last_month.strftime('%B %Y')}"
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                            .container {{ max-width: 700px; margin: 0 auto; background: white; border-radius: 10px; }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .stats {{ display: flex; justify-content: space-around; padding: 20px; background: #f8f9fa; }}
                            .stat-box {{ text-align: center; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); flex: 1; margin: 0 10px; }}
                            .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                            .content {{ padding: 30px; }}
                            .booking-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                            .booking-table th, .booking-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                            .booking-table th {{ background-color: #007bff; color: white; }}
                            .booking-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>UrbanPark Monthly Report</h1>
                                <h2>{user.full_name}</h2>
                                <p>Activity Report for {start_of_last_month.strftime('%B %Y')}</p>
                            </div>
                            
                            <div class="stats">
                                <div class="stat-box">
                                    <div class="stat-number">{total_bookings}</div>
                                    <p>Total Bookings</p>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-number">{completed_bookings}</div>
                                    <p>Completed</p>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-number">₹{total_spent:.2f}</div>
                                    <p>Total Spent</p>
                                </div>
                            </div>
                            
                            <div class="content">
                                <h3>📊 Summary</h3>
                                <p><strong>Most Used Parking Lot:</strong> {most_used_lot}</p>
                                <p><strong>Average Cost per Booking:</strong> ₹{(total_spent/total_bookings):.2f}</p>
                                
                                <h3>📋 Detailed Booking History</h3>
                                <table class="booking-table">
                                    <tr>
                                        <th>Date</th>
                                        <th>Parking Lot</th>
                                        <th>Spot ID</th>
                                        <th>Vehicle</th>
                                        <th>Duration</th>
                                        <th>Cost</th>
                                    </tr>
                                    {''.join([
                                        f'''<tr>
                                            <td>{r.parking_timestamp.strftime("%Y-%m-%d")}</td>
                                            <td>{r.parking_spot.parking_lot.prime_location_name}</td>
                                            <td>{r.spot_id}</td>
                                            <td>{r.vehicle_number}</td>
                                            <td>{f"{((r.leaving_timestamp - r.parking_timestamp).total_seconds() / 3600):.1f}h" if r.leaving_timestamp else "Ongoing"}</td>
                                            <td>₹{r.parking_cost or 0:.2f}</td>
                                        </tr>''' 
                                        for r in reservations
                                    ])}
                                </table>
                                
                                <div style="text-align: center; margin-top: 30px;">
                                    <a href="http://localhost:8080" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Visit UrbanPark Dashboard</a>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    # Send email
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        html=html_content
                    )
                    mail.send(msg)
                    sent_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to send monthly report to {user.email}: {e}")
                    continue
            
            return f"Monthly reports sent to {sent_count} users"
            
        except Exception as e:
            logging.error(f"Monthly report task failed: {e}")
            return f"Monthly report task failed: {str(e)}"

@celery.task(name='app.export_user_data_csv')
def export_user_data_csv(user_id, job_id):
    """Export user parking data as CSV"""
    with app.app_context():
        try:
            # Update job status to processing
            job = ExportJob.query.get(job_id)
            if job:
                job.status = 'processing'
                db.session.commit()
            
            user = User.query.get(user_id)
            if not user:
                if job:
                    job.status = 'failed'
                    job.error_message = 'User not found'
                    db.session.commit()
                return "User not found"
            
            reservations = ReserveParkingSpot.query.filter_by(user_id=user_id).order_by(
                ReserveParkingSpot.parking_timestamp.desc()
            ).all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Reservation ID', 'Slot ID', 'Spot ID', 'Parking Lot', 'Spot Number',
                'Vehicle Number', 'Parking Timestamp', 'Leaving Timestamp', 
                'Duration (hours)', 'Cost (₹)', 'Status', 'Remarks'
            ])
            
            # Write data
            for reservation in reservations:
                duration = ''
                if reservation.leaving_timestamp:
                    duration = f"{((reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600):.1f}"
                
                writer.writerow([
                    reservation.id,
                    reservation.parking_spot.lot_id,
                    reservation.spot_id,
                    reservation.parking_spot.parking_lot.prime_location_name,
                    reservation.parking_spot.spot_number,
                    reservation.vehicle_number,
                    reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    reservation.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if reservation.leaving_timestamp else '',
                    duration,
                    reservation.parking_cost or '',
                    reservation.status,
                    reservation.remarks or ''
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            # Create filename and save path
            filename = f'parking_data_{user.full_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            # Creating email with CSV file attached
            subject = "🅿️ Your Parking Data Export is Ready"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #007bff;">UrbanPark - Data Export Complete</h2>
                    <p>Hi {user.full_name},</p>
                    <p>Your parking data export has been completed successfully!</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>📊 Export Summary:</h3>
                        <ul>
                            <li><strong>Total Records:</strong> {len(reservations)}</li>
                            <li><strong>Export Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>File Format:</strong> CSV</li>
                        </ul>
                    </div>
                    
                    <p><strong>The CSV file contains:</strong></p>
                    <ul>
                        <li>All your parking reservations</li>
                        <li>Parking timestamps and durations</li>
                        <li>Cost breakdown for each booking</li>
                        <li>Vehicle details and spot information</li>
                        <li>Status and remarks</li>
                    </ul>
                    
                    <p>The CSV file is attached to this email.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:8080/dashboard" style="background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">Visit Dashboard</a>
                    </div>
                    
                    <hr style="margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        Best regards,<br>
                        UrbanPark Team
                    </p>
                </div>
            </body>
            </html>
            """
            # Send email with attachment
            msg = Message(
                subject=subject,
                recipients=[user.email],
                html=html_content
            )
            
            # Attach CSV file
            msg.attach(
                filename,
                "text/csv",
                csv_content
            )
            
            mail.send(msg)
            
            # Update job status to completed
            if job:
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.file_path = filename
                db.session.commit()
            
            return f"CSV export completed and sent to {user.full_name}"
            
        except Exception as e:
            logging.error(f"CSV export task failed: {e}")
            
            # Update job status to failed
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                db.session.commit()
            
            return f"CSV export task failed: {str(e)}"

def send_daily_reminders_manual():
    """Send daily reminders to ALL users when admin clicks and it sends whether active or not"""
    with app.app_context():
        try:
            # Get ALL regular users (not just inactive ones)
            all_users = db.session.query(User).filter(
                User.is_admin == False
            ).all()
            
            available_lots = db.session.query(ParkingLot).join(ParkingSpot).filter(
                ParkingSpot.status == 'A'
            ).distinct().limit(5).all()
            
            sent_count = 0
            for user in all_users:
                try:
                    subject = "UrbanPark - Manual Daily Reminder (Admin Triggered)"
                    html_content = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; border: 2px solid #007bff;">
                            <div style="background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                                <h1>UrbanPark Manual Reminder</h1>
                                <p><strong>⚡ Sent by Admin on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                            </div>
                            <div style="padding: 20px;">
                                <h2>Hi {user.full_name},</h2>
                                <p>Our admin wanted to personally remind ALL users about available parking spots!</p>
                                
                                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                    <p><strong>📢 This is a manual broadcast message sent to all users!</strong></p>
                                </div>
                                
                                <h3>🅿️ Available Parking Spots Right Now:</h3>
                                {''.join([f'''
                                <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; background: #f8f9fa;">
                                    <strong>{lot.prime_location_name}</strong><br>
                                    <small>{lot.address}</small><br>
                                    <span style="color: #28a745; font-weight: bold;">₹{lot.price}/hour</span>
                                </div>
                                ''' for lot in available_lots])}
                                
                                <p style="text-align: center; margin-top: 30px;">
                                    <a href="http://localhost:8080/parking-lots" style="background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">Book Parking Now</a>
                                </p>
                                
                                <hr style="margin: 30px 0;">
                                <p style="font-size: 12px; color: #666; text-align: center;">
                                    📧 This reminder was manually sent by admin to ALL users. Automatic reminders are sent only to inactive users.
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        html=html_content
                    )
                    mail.send(msg)
                    sent_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to send manual reminder to {user.email}: {e}")
                    continue
            
            return f"Manual daily reminders sent to ALL {sent_count} users"
            
        except Exception as e:
            return f"Manual daily reminder failed: {str(e)}"

def send_monthly_reports_manual():
    """Send monthly reports to ALL users when admin clicks"""
    with app.app_context():
        try:
            now = datetime.utcnow()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
            
            # Get ALL users (not just those with activity)
            all_users = db.session.query(User).filter(User.is_admin == False).all()
            sent_count = 0
            
            for user in all_users:
                try:
                    # Get user's bookings for last month
                    reservations = db.session.query(ReserveParkingSpot).filter(
                        ReserveParkingSpot.user_id == user.id,
                        ReserveParkingSpot.parking_timestamp >= start_of_last_month,
                        ReserveParkingSpot.parking_timestamp < start_of_month
                    ).all()
                    
                    # Calculate statistics (even if 0 bookings)
                    total_bookings = len(reservations)
                    total_spent = sum(r.parking_cost or 0 for r in reservations)
                    completed_bookings = len([r for r in reservations if r.status == 'completed'])
                    
                    if reservations:
                        # Has activity - send detailed report
                        lot_usage = {}
                        for r in reservations:
                            lot_name = r.parking_spot.parking_lot.prime_location_name
                            lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
                        most_used_lot = max(lot_usage.items(), key=lambda x: x[1])[0] if lot_usage else "None"
                        avg_cost = total_spent / total_bookings if total_bookings > 0 else 0
                        
                        activity_section = f"""
                        <div style="display: flex; justify-content: space-around; padding: 20px; background: #f8f9fa; margin-bottom: 20px; border-radius: 10px;">
                            <div style="text-align: center; padding: 15px;">
                                <div style="font-size: 2em; font-weight: bold; color: #007bff;">{total_bookings}</div>
                                <p>Total Bookings</p>
                            </div>
                            <div style="text-align: center; padding: 15px;">
                                <div style="font-size: 2em; font-weight: bold; color: #007bff;">{completed_bookings}</div>
                                <p>Completed</p>
                            </div>
                            <div style="text-align: center; padding: 15px;">
                                <div style="font-size: 2em; font-weight: bold; color: #007bff;">₹{total_spent:.2f}</div>
                                <p>Total Spent</p>
                            </div>
                        </div>
                        
                        <h3>📊 Summary</h3>
                        <p><strong>Most Used Parking Lot:</strong> {most_used_lot}</p>
                        <p><strong>Average Cost per Booking:</strong> ₹{avg_cost:.2f}</p>
                        """
                    else:
                        # No activity - send encouragement
                        activity_section = f"""
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 20px 0;">
                            <h3>📊 Your Activity Summary</h3>
                            <p><strong>No parking bookings in {start_of_last_month.strftime('%B %Y')}</strong></p>
                            <p>Don't miss out on convenient parking! Check out our available spots.</p>
                        </div>
                        """
                    
                    subject = f"Manual Monthly Report - {start_of_last_month.strftime('%B %Y')} (Admin Broadcast)"
                    html_content = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <div style="max-width: 700px; margin: 0 auto; background: white; border-radius: 10px; border: 2px solid #007bff;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                                <h1>UrbanPark Manual Monthly Report</h1>
                                <h2>{user.full_name}</h2>
                                <p>Manual Report for {start_of_last_month.strftime('%B %Y')}</p>
                                <p><strong>⚡ Sent by Admin to ALL users on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                            </div>
                            
                            <div style="padding: 30px;">
                                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                    <p><strong>📢 This is a manual broadcast report sent to all users!</strong></p>
                                </div>
                                
                                {activity_section}
                                
                                <div style="text-align: center; margin-top: 30px;">
                                    <a href="http://localhost:8080" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Visit UrbanPark Dashboard</a>
                                </div>
                                
                                <hr style="margin: 30px 0;">
                                <p style="font-size: 12px; color: #666; text-align: center;">
                                    📧 This report was manually sent by admin to ALL users. Automatic monthly reports are sent only to users with activity.
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        html=html_content
                    )
                    mail.send(msg)
                    sent_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to send manual report to {user.email}: {e}")
                    continue
            
            return f"Manual monthly reports sent to ALL {sent_count} users"
            
        except Exception as e:
            return f"Manual monthly report failed: {str(e)}"

# CSV Export Routes
@app.route('/api/export-csv', methods=['POST'])
def trigger_csv_export():
    if not is_logged_in():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = session['user_id']
        
        # Create export job record
        job_id = f"csv_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_job = ExportJob(
            id=job_id,
            user_id=user_id,
            job_type='csv_export',
            status='pending'
        )
        db.session.add(export_job)
        db.session.commit()
        
        task_result = export_user_data_csv.delay(user_id, job_id)
        
        return jsonify({
            'message': 'CSV export started! You will receive an email when ready.',
            'job_id': job_id,
            'task_id': task_result.id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#user seeing lots route

@app.route('/api/parking-lots', methods=['GET'])
def get_parking_lots():
    """Get parking lots for regular users"""
    try:
        cache_key = "user_parking_lots"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            return jsonify(cached_data), 200
        
        lots = ParkingLot.query.all()
        lots_data = []
        
        for lot in lots:
            spots_data = []
            for spot in lot.parking_spots:
                spots_data.append({
                    'id': spot.id,
                    'spot_number': spot.spot_number,
                    'status': spot.status
                })
            
            lot_dict = {
                'id': lot.id,
                'prime_location_name': lot.prime_location_name,
                'price': lot.price,
                'address': lot.address,
                'pin_code': lot.pin_code,
                'number_of_spots': lot.number_of_spots,
                'available_spots': len([s for s in lot.parking_spots if s.status == 'A']),
                'occupied_spots': len([s for s in lot.parking_spots if s.status == 'O']),
                'spots': spots_data 
            }
            lots_data.append(lot_dict)
        
        # Cache for 2 minutes
        set_cache(cache_key, lots_data, 120)
        
        return jsonify(lots_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/book-parking', methods=['POST'])
def book_parking():
    """Book a parking spot"""
    if not is_logged_in():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        lot_id = data.get('lot_id')
        vehicle_number = data.get('vehicle_number')
        
        if not lot_id or not vehicle_number:
            return jsonify({'error': 'Lot ID and vehicle number are required'}), 400
        
        # Check if user already has an active reservation
        existing_reservation = ReserveParkingSpot.query.filter_by(
            user_id=session['user_id'],
            status='active'
        ).first()
        
        if existing_reservation:
            return jsonify({'error': 'You already have an active booking'}), 400
        
        # Find an available spot
        available_spot = ParkingSpot.query.filter_by(
            lot_id=lot_id,
            status='A'
        ).first()
        
        if not available_spot:
            return jsonify({'error': 'No available spots'}), 400
        
        # Create reservation
        reservation = ReserveParkingSpot(
            spot_id=available_spot.id,
            user_id=session['user_id'],
            vehicle_number=vehicle_number,
            parking_timestamp=datetime.utcnow(),
            status='active'
        )
        
        # Update spot status
        available_spot.status = 'O'
        
        db.session.add(reservation)
        db.session.commit()
        
        # Clear caches
        delete_cache("admin_parking_lots", "user_parking_lots", f"user_dashboard_stats_{session['user_id']}")
        
        return jsonify({
            'message': 'Booking successful',
            'reservation': {
                'id': reservation.id,
                'spot_id': available_spot.id,
                'spot_number': available_spot.spot_number,
                'parking_lot': available_spot.parking_lot.prime_location_name,
                'vehicle_number': vehicle_number,
                'parking_timestamp': reservation.parking_timestamp.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-reservations', methods=['GET'])
def get_my_reservations():
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        user_id = session['user_id']
        
        # Get reservations with parking lot information
        reservations = db.session.query(ReserveParkingSpot).join(
            ParkingSpot
        ).join(
            ParkingLot
        ).filter(
            ReserveParkingSpot.user_id == user_id
        ).order_by(
            ReserveParkingSpot.parking_timestamp.desc()
        ).all()
        
        data = []
        for r in reservations:
            lot = r.parking_spot.parking_lot
            
            # Calculate duration and cost
            if r.status == 'completed' and r.leaving_timestamp:
                duration = (r.leaving_timestamp - r.parking_timestamp).total_seconds()
                cost = r.parking_cost or 0
            else:
                # For active reservations, calculate current duration
                now_ist = datetime.now(IST)
                parking_time = r.parking_timestamp
                
                if parking_time.tzinfo is None:
                    parking_time = IST.localize(parking_time)
                else:
                    parking_time = parking_time.astimezone(IST)
                
                duration = max(0, (now_ist - parking_time).total_seconds())
                cost = (duration / 3600) * float(lot.price)
            
            hours = int(duration // 3600)
            mins = int((duration % 3600) // 60)
            
            data.append({
                'id': r.id,
                'spot_id': r.spot_id,
                'lot_name': lot.prime_location_name,
                'lot_address': lot.address,
                'lot_price': float(lot.price),
                'vehicle_number': r.vehicle_number,
                'parking_timestamp': r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'leaving_timestamp': r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else None,
                'parking_cost': round(cost, 2),
                'status': r.status,
                'duration_display': f"{hours}h {mins}m",
                'duration_seconds': int(duration)
            })
        
        print(f"✅ Found {len(data)} reservations for user {user_id}")
        return jsonify(data), 200
        
    except Exception as e:
        print(f"❌ Error in get_my_reservations: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/release-parking/<int:reservation_id>', methods=['POST'])
def release_parking(reservation_id):
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        user_id = session['user_id']
        
        reservation = ReserveParkingSpot.query.filter_by(
            id=reservation_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not reservation:
            return jsonify({'error': 'Reservation not found or already completed'}), 404
        
        now_ist = datetime.now(IST)
        
        parking_time = reservation.parking_timestamp
        if parking_time.tzinfo is None:
            parking_time = IST.localize(parking_time)
        else:
            parking_time = parking_time.astimezone(IST)
        
        duration = now_ist - parking_time
        hours_parked = max(0, duration.total_seconds() / 3600)  # Prevent negative
        
        # Calculate cost
        lot = reservation.parking_spot.parking_lot
        parking_cost = hours_parked * float(lot.price)
        
        # Apply minimum cost for very short durations
        if duration.total_seconds() < 360:  # Less than 6 minutes
            parking_cost = max(1.0, parking_cost)
        
        # Update reservation
        reservation.leaving_timestamp = now_ist
        reservation.parking_cost = round(parking_cost, 2)
        reservation.status = 'completed'
        
        # Update spot status
        spot = reservation.parking_spot
        spot.status = 'A'
        
        db.session.commit()
        
        # Clear caches
        delete_cache(
            "admin_parking_lots",
            "user_parking_lots", 
            "admin_dashboard_stats",
            f"user_dashboard_stats_{user_id}"
        )
        
        # Format response times consistently
        duration_hours = int(hours_parked)
        duration_mins = int((hours_parked % 1) * 60)
        
        return jsonify({
            'message': 'Parking released successfully',
            'parking_time': parking_time.strftime('%d/%m/%Y, %I:%M:%S %p'),
            'leaving_time': now_ist.strftime('%d/%m/%Y, %I:%M:%S %p'),
            'duration': f"{duration_hours}h {duration_mins}m",
            'cost': round(parking_cost, 2),
            'hours_parked': round(hours_parked, 1)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Release parking error: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/dashboard-stats', methods=['GET'])
def get_admin_dashboard_stats():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Simple version without caching
        total_lots = ParkingLot.query.count()
        total_spots = ParkingSpot.query.count()
        available_spots = ParkingSpot.query.filter_by(status='A').count()
        occupied_spots = ParkingSpot.query.filter_by(status='O').count()
        total_users = User.query.filter_by(is_admin=False).count()
        
        stats = {
            'total_lots': total_lots,
            'total_spots': total_spots,
            'available_spots': available_spots,
            'occupied_spots': occupied_spots,
            'total_users': total_users
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Get all users for admin"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        users = User.query.filter_by(is_admin=False).all()
        users_data = [user.to_dict() for user in users]
        
        return jsonify(users_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/search-lots', methods=['GET'])
def search_parking_lots():
    """Search parking lots by name"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify([]), 200
        
        lots = ParkingLot.query.filter(
            ParkingLot.prime_location_name.ilike(f'%{query}%')
        ).all()
        
        results = []
        for lot in lots:
            results.append({
                'id': lot.id,
                'prime_location_name': lot.prime_location_name,
                'address': lot.address
            })
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/spot-details/<int:spot_id>', methods=['GET'])
def get_spot_details(spot_id):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    try:
        spot = ParkingSpot.query.get_or_404(spot_id)

        spot_data = {
            'id': spot.id,
            'spot_number': spot.spot_number,
            'status': spot.status,
            'lot_name': spot.parking_lot.prime_location_name,
            'reservation': None
        }

        if spot.status == 'O':
            reservation = ReserveParkingSpot.query.filter_by(
                spot_id=spot_id,
                status='active'
            ).first()

            if reservation:
                # Get current IST time
                now_ist = datetime.now(IST)
                
                # Ensure parking time is in IST
                parking_time = reservation.parking_timestamp
                if parking_time.tzinfo is None:
                    parking_time = IST.localize(parking_time)
                else:
                    parking_time = parking_time.astimezone(IST)
                
                # Calculate duration - both times are now timezone-aware
                duration = now_ist - parking_time
                duration_seconds = max(0, duration.total_seconds())
                hours_parked = duration_seconds / 3600
                
                # Calculate cost
                estimated_cost = max(0.0, hours_parked * spot.parking_lot.price)
                
                spot_data['reservation'] = {
                    'user_id': reservation.user_id,
                    'user_name': reservation.user.full_name,
                    'user_email': reservation.user.email,
                    'vehicle_number': reservation.vehicle_number,
                    'parking_timestamp': parking_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'hours_parked': round(max(0.0, hours_parked), 1),
                    'estimated_cost': round(estimated_cost, 2)
                }

        return jsonify(spot_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/spots/<int:spot_id>', methods=['DELETE'])
def delete_spot(spot_id):
    """Delete a parking spot (only if available)"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        spot = ParkingSpot.query.get(spot_id)
        
        if not spot:
            return jsonify({'error': 'Spot not found'}), 404
        
        if spot.status == 'O':
            return jsonify({'error': 'Cannot delete occupied spot'}), 400
        
        # Update parking lot spot count
        parking_lot = spot.parking_lot
        parking_lot.number_of_spots -= 1
        
        db.session.delete(spot)
        db.session.commit()
        
        # Clear caches
        delete_cache("admin_parking_lots", "user_parking_lots", "admin_dashboard_stats")
        
        return jsonify({'message': 'Spot deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# spot edit route

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['PUT'])
def update_parking_lot(lot_id):
    """Update parking lot details"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json()
        lot = ParkingLot.query.get(lot_id)
        
        if not lot:
            return jsonify({'error': 'Parking lot not found'}), 404
        
        # Update lot details
        lot.prime_location_name = data.get('prime_location_name', lot.prime_location_name)
        lot.price = float(data.get('price', lot.price))
        lot.address = data.get('address', lot.address)
        lot.pin_code = data.get('pin_code', lot.pin_code)
        
        # Handle spot count changes
        new_spot_count = int(data.get('number_of_spots', lot.number_of_spots))
        current_spot_count = len(lot.parking_spots)
        
        if new_spot_count > current_spot_count:
            # Add new spots
            for i in range(current_spot_count + 1, new_spot_count + 1):
                new_spot = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=i,
                    status='A'
                )
                db.session.add(new_spot)
        elif new_spot_count < current_spot_count:
            # Remove spots (only available ones)
            spots_to_remove = ParkingSpot.query.filter_by(
                lot_id=lot.id,
                status='A'
            ).order_by(ParkingSpot.spot_number.desc()).limit(
                current_spot_count - new_spot_count
            ).all()
            
            for spot in spots_to_remove:
                db.session.delete(spot)
        
        lot.number_of_spots = new_spot_count
        
        db.session.commit()
        
        # Clear caches
        delete_cache("admin_parking_lots", "user_parking_lots", "admin_dashboard_stats")
        
        return jsonify({'message': 'Parking lot updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/user-dashboard-stats', methods=['GET'])
def get_user_dashboard_stats():
    """Get user dashboard statistics"""
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        user_id = session['user_id']
        
        # Get user's reservations
        reservations = ReserveParkingSpot.query.filter_by(user_id=user_id).all()
        
        total_bookings = len(reservations)
        active_bookings = len([r for r in reservations if r.status == 'active'])
        completed_bookings = len([r for r in reservations if r.status == 'completed'])
        total_spent = sum(r.parking_cost or 0 for r in reservations if r.parking_cost)
        
        stats = {
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'total_spent': round(total_spent, 2)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['DELETE'])
def delete_parking_lot(lot_id):
    """Delete parking lot"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        lot = ParkingLot.query.get(lot_id)
        
        if not lot:
            return jsonify({'error': 'Parking lot not found'}), 404
        
        # Check if any spots are occupied
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
        
        if occupied_spots > 0:
            return jsonify({'error': 'Cannot delete parking lot with occupied spots'}), 400
        
        db.session.delete(lot)
        db.session.commit()
        
        # Clear caches
        delete_cache("admin_parking_lots", "user_parking_lots", "admin_dashboard_stats")
        
        return jsonify({'message': 'Parking lot deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/reserve-parking/<int:spot_id>', methods=['POST'])
def reserve_parking(spot_id):
    if not is_logged_in():
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        # CHECK FOR EXISTING ACTIVE RESERVATION 
        existing_reservation = ReserveParkingSpot.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if existing_reservation:
            return jsonify({'error': 'You already have an active booking. Please release it first.'}), 400
        
        spot = ParkingSpot.query.get_or_404(spot_id)
        if spot.status != 'A':
            return jsonify({'error': 'Parking spot is not available'}), 400
       
        now = datetime.now(IST)
        
        reservation = ReserveParkingSpot(
            user_id=user_id,
            spot_id=spot_id,
            vehicle_number=data['vehicle_number'],
            parking_timestamp=now,
            status='active'
        )
        
        spot.status = 'O'
        db.session.add(reservation)
        db.session.commit()
        
        # Clear caches
        delete_cache("admin_parking_lots", "user_parking_lots", f"user_dashboard_stats_{user_id}")
        
        return jsonify({
            'message': 'Parking spot reserved successfully',
            'reservation_id': reservation.id,
            'spot_id': spot_id,
            'parking_time': now.strftime('%d/%m/%Y, %I:%M:%S %p'),
            'vehicle_number': data['vehicle_number'],
            'lot_name': spot.parking_lot.prime_location_name,
            'lot_address': spot.parking_lot.address,
            'lot_price': float(spot.parking_lot.price)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# gives charts data in admin dashboard

@app.route('/api/admin/charts-data', methods=['GET'])
def get_admin_charts_data():
    """Get data for admin charts"""
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get all parking lots
        lots = ParkingLot.query.all()
        
        bar_labels = []
        available_data = []
        occupied_data = []
        
        for lot in lots:
            bar_labels.append(lot.prime_location_name)
            
            available_count = 0
            occupied_count = 0
            
            for spot in lot.parking_spots:
                if spot.status == 'A':
                    available_count += 1
                elif spot.status == 'O':
                    occupied_count += 1
            
            available_data.append(available_count)
            occupied_data.append(occupied_count)
        
        # Pie chart data - Show actual revenue per lot
        pie_labels = bar_labels if bar_labels else ['No Parking Lots']
        pie_revenue = []

        for lot in lots:
            # Calculate total revenue for this lot
            lot_revenue = db.session.query(db.func.sum(ReserveParkingSpot.parking_cost)).join(
                ParkingSpot
            ).filter(
                ParkingSpot.lot_id == lot.id,
                ReserveParkingSpot.status == 'completed',
                ReserveParkingSpot.parking_cost.isnot(None)
            ).scalar() or 0
            
            pie_revenue.append(float(lot_revenue))

        if not pie_revenue or all(rev == 0 for rev in pie_revenue):
            pie_revenue = [0]
            pie_labels = ['No Revenue Data']
        
        charts_data = {
            'bar_chart': {
                'labels': bar_labels,
                'available': available_data,
                'occupied': occupied_data
            },
            'pie_chart': {
                'labels': pie_labels,
                'revenue': pie_revenue
            }
        }
        
        return jsonify(charts_data), 200
        
    except Exception as e:
        print(f"Charts data error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Return safe fallback data
        return jsonify({
            'bar_chart': {
                'labels': ['No Data'],
                'available': [0],
                'occupied': [0]
            },
            'pie_chart': {
                'labels': ['No Revenue Data'],
                'revenue': [0]
            }
        }), 200

@app.route('/api/export-status/<job_id>', methods=['GET'])
def get_export_status(job_id):
    """Check the status of export job"""
    if not is_logged_in():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        job = ExportJob.query.filter_by(id=job_id, user_id=session['user_id']).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.id,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-export-jobs', methods=['GET'])
def get_my_export_jobs():
    """Get all export jobs for current user"""
    if not is_logged_in():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        jobs = ExportJob.query.filter_by(user_id=session['user_id']).order_by(
            ExportJob.created_at.desc()
        ).limit(10).all()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job.id,
                'job_type': job.job_type,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message
            })
        
        return jsonify(jobs_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin manual trigger routes
@app.route('/api/admin/trigger-daily-reminders', methods=['POST'])
def trigger_manual_daily_reminders():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Call manual function for immediate sending
        result = send_daily_reminders_manual()
        return jsonify({
            'message': result,
            'status': 'sent_immediately',
            'note': 'Automatic daily reminders continue running as scheduled'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/trigger-monthly-reports', methods=['POST'])
def trigger_manual_monthly_reports():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Call manual function for immediate sending
        result = send_monthly_reports_manual()
        return jsonify({
            'message': result,
            'status': 'sent_immediately',
            'note': 'Automatic monthly reports continue running as scheduled'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Initialize database and create admin user
def create_admin_user():
    """Create default admin user"""
    admin = User.query.filter_by(email='admin@parking.com').first()
    if not admin:
        admin = User(
            email='admin@parking.com',
            full_name='Admin',
            phone='9999999999',
            address='Admin Office',
            pin_code='000000',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@parking.com / admin123")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(debug=True, host='0.0.0.0', port=5000)
