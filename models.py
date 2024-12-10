from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Zone(db.Model):
    __tablename__ = 'zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    units = db.relationship('Unit', backref='zone', lazy=True, cascade='all, delete-orphan')
    zone_users = db.relationship('User', backref='assigned_zone', lazy=True, foreign_keys='User.zone_id')
    director = db.relationship('User', foreign_keys=[director_id], backref='directed_zone', lazy=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Zone {self.name}>'

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    centers = db.relationship('Center', backref='unit', lazy=True, cascade='all, delete-orphan')
    unit_users = db.relationship('User', backref='assigned_unit', lazy=True, foreign_keys='User.unit_id')
    director = db.relationship('User', foreign_keys=[director_id], backref='directed_unit', lazy=True)
    incidents = db.relationship('Incident', backref='unit', lazy=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Unit {self.name}>'

class Center(db.Model):
    __tablename__ = 'centers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Foreign Keys
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='CASCADE'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Center {self.name}>'

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    professional_number = db.Column(db.String(50), unique=True, nullable=False)
    job_function = db.Column(db.String(100), nullable=False)
    recruitment_date = db.Column(db.DateTime, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
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
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='Employeur de l\'unité')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Foreign Keys
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id', ondelete='SET NULL'), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    incidents = db.relationship('Incident', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
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
    resolution_notes = db.Column(db.Text)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    center_id = db.Column(db.Integer, db.ForeignKey('centers.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Incident {self.id}>'
