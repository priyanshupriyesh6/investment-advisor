from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import json
from investment_logic import InvestmentAdvisor

import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'investment-advisor-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///investment.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Security features
csrf = CSRFProtect(app)
Talisman(app, content_security_policy=None)
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per hour"])

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure the instance folder exists
import os
if not os.path.exists('instance'):
    os.makedirs('instance')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    plans = db.relationship('InvestmentPlan', backref='user', lazy=True)

class InvestmentPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    time_period = db.Column(db.Integer, nullable=False)
    investment_type = db.Column(db.String(20), nullable=False)
    risk_tolerance = db.Column(db.String(20), nullable=False)
    monthly_increment = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recommendations = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/api/calculate', methods=['POST'])
@limiter.limit("10 per minute")
def calculate():
    try:
        data = request.get_json()
        if not data:
            abort(400, description='No data provided')

        required_fields = ['amount', 'time_period', 'investment_type', 'risk_tolerance']
        for field in required_fields:
            if field not in data:
                abort(400, description=f'Missing required field: {field}')

        advisor = InvestmentAdvisor()
        advice = advisor.get_investment_advice(
            float(data['amount']),
            int(data['time_period']),
            data['investment_type'],
            data['risk_tolerance'],
            float(data.get('monthly_increment', 0))
        )
        strategy = advisor.explain_investment_strategy(advice, data['risk_tolerance'])

        # Save to database if user is authenticated
        if current_user.is_authenticated:
            plan = InvestmentPlan(
                user_id=current_user.id,
                amount=float(data['amount']),
                time_period=int(data['time_period']),
                investment_type=data['investment_type'],
                risk_tolerance=data['risk_tolerance'],
                monthly_increment=float(data.get('monthly_increment', 0)),
                recommendations=json.dumps(advice)
            )
            db.session.add(plan)
            db.session.commit()

        return jsonify({
            'advice': advice,
            'strategy': strategy
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500
    
    if current_user.is_authenticated:
        plan = InvestmentPlan(
            user_id=current_user.id,
            amount=float(data['amount']),
            time_period=int(data['time_period']),
            investment_type=data['investment_type'],
            risk_tolerance=data['risk_tolerance'],
            monthly_increment=float(data.get('monthly_increment', 0)),
            recommendations=json.dumps(advice)
        )
        db.session.add(plan)
        db.session.commit()
    
    return jsonify({
        'advice': advice,
        'strategy': strategy
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        admin_email = 'admin@example.com'  # Set your admin email here
        is_admin = (email == admin_email)
        user = User(
            username=request.form['username'],
            email=email,
            password=request.form['password'],  # In production, hash the password
            is_admin=is_admin
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:  # In production, verify hashed password
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    plans = InvestmentPlan.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', plans=plans)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

def create_tables():
    with app.app_context():
        db.create_all()

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': error.description}), 400

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error.'}), 500

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='127.0.0.1', port=5000)