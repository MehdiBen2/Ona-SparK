from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    users = db.relationship('User', backref='unit', lazy=True)
    incidents = db.relationship('Incident', backref='unit', lazy=True)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    professional_number = db.Column(db.String(50), unique=True, nullable=False)
    job_function = db.Column(db.String(100), nullable=False)
    recruitment_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_years_of_work(self):
        today = datetime.now()
        years = today.year - self.recruitment_date.year
        if today.month < self.recruitment_date.month or (today.month == self.recruitment_date.month and today.day < self.recruitment_date.day):
            years -= 1
        return years

    def calculate_age(self):
        today = datetime.now()
        years = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            years -= 1
        return years

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Unit Officer')
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    incidents = db.relationship('Incident', backref='author', lazy=True)
    profile = db.relationship('UserProfile', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wilaya = db.Column(db.String(50), nullable=False)
    commune = db.Column(db.String(100), nullable=False)
    localite = db.Column(db.String(200), nullable=False)
    nature_cause = db.Column(db.Text, nullable=False)
    date_incident = db.Column(db.DateTime, nullable=False)
    mesures_prises = db.Column(db.Text)  
    impact = db.Column(db.Text, nullable=False)
    gravite = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Nouveau')
    date_resolution = db.Column(db.DateTime)  
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
