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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Unit Officer')
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    incidents = db.relationship('Incident', backref='author', lazy=True)

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
