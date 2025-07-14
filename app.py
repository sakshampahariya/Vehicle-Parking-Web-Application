from flask import Flask, flash, render_template, request, url_for,redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash , check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SECRET_KEY'] = '28d5972b820e8fe04b048c698fee0e7a'
db= SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(180), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    is_admin = db.Column(db.Boolean, default=False)
    reservation = db.relationship("ReserveParkingSpot", backref="user", cascade='all, delete')

    def set_password(self , password):
        self.password_hash = generate_password_hash(password)
    def check_password(self , password):
        return check_password_hash(self.password_hash , password)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True , nullable = False)
    location = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Integer , nullable = False , default = 0)
    address = db.Column(db.String(180), nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    num_of_spots = db.Column(db.Integer , nullable = False , default = 0)
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', cascade="all, delete")
    

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True , nullable= False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')
    reservation = db.relationship('ReserveParkingSpot', backref='parking_spot', cascade="all, delete")

class ReserveParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True , nullable= False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parkingtimestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leaving = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Integer, nullable=True)
    vehicle_num = db.Column(db.String(20), nullable=False)
    
    # parking_spot = db.relationship('Parking_spot', backref="reserve", cascade = "all, delete", lazy=True)
    # user = db.relationship("User", backref="reserve")

class RecentBookings(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reserve_parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    booking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(1), nullable=False, default='A')
    
    
    reservation = db.relationship("ReserveParkingSpot", backref="recent_booking")
    user = db.relationship("User", backref="recent_bookings")
    parking_lot = db.relationship("ParkingLot", backref="recent_bookings")
    parking_spot = db.relationship("ParkingSpot", backref="recent_bookings")
    


# USER: ID, EMAIL, PASSWORD, FULLNAME, ADDRESS, PINCODE, IS_ADMIN
# PARKING_LOT: ID, LOCATION, PRICE, ADDRESS, PINCODE, NUMBER_OF_SPOTS
# PARKING_SPOT: ID, LOT_ID(FK), SPOT_NUMBER, STATUS
# RESERVE_PARKING_SPOT: ID, SPOT_ID(FK), USER_ID(FK), PARKINGTIMESTAMP, LEAVING, PARKING_COST, VEHICLE_NUM
# RECENT_BOOKINGS: ID, RESERVATION_ID(FK), USER_ID(FK), LOT_ID(FK), SPOT_ID(FK), BOOKING_TIMESTAMP, STATUS

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin():
    with app.app_context():
        admin = User.query.filter_by(email='admin@quizmaster.com').first()
        if not admin:
            admin = User(
                email='admin@quizmaster.com',
                full_name='Quizer Admin',
                address='bhagwan',
                pincode=000000,
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

@app.route("/")
@app.route("/home")

def home():
    pass

@app.route("/login", methods= ['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admindash'))
            else:
                return redirect(url_for('user_dash'))
        else:
            flash('Invalid Username or Password')
            return redirect(url_for('landing'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = User(
            email=request.form['email'],
            full_name=request.form['name'],
            address=request.form['Address'],
            pincode= request.form['Pincode'],
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
    app.run( debug=True )