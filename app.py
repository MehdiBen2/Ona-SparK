from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from utils.pdf_generator import create_incident_pdf
import random
from functools import wraps
from openpyxl import Workbook
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from models import db, User, Unit, Incident
from routes.auth import auth
from routes.profiles import profiles

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ona_incidents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(profiles)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Water and sanitation phrases
WATER_PHRASES = [
    "L'eau est l'essence de la vie ; préservons-la pour les générations futures.",
    "L'assainissement est une question de dignité ; assurons-le pour tous.",
    "Chaque goutte compte ; économisez l'eau dès aujourd'hui.",
    "De l'eau propre, des vies saines.",
    "Un bon assainissement prévient les maladies ; c'est notre responsabilité partagée.",
    "L'accès à l'eau potable est un droit humain.",
    "L'assainissement est la clé d'un avenir durable.",
    "L'eau soutient la vie ; gardons-la propre.",
    "L'hygiène, c'est la santé ; priorisons l'assainissement.",
    "Ensemble, nous pouvons rendre l'eau potable et l'assainissement accessibles à tous."
]

# Routes
@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/main')
@login_required
def main_dashboard():
    # Get recent incidents (last 5)
    if current_user.role == 'Admin':
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
    else:
        recent_incidents = Incident.query.filter_by(author=current_user).order_by(Incident.date_incident.desc()).limit(5).all()
    
    # Get statistics
    if current_user.role == 'Admin':
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
        pending_incidents = Incident.query.filter_by(status='En cours').count()
    else:
        total_incidents = Incident.query.filter_by(author=current_user).count()
        resolved_incidents = Incident.query.filter_by(author=current_user, status='Résolu').count()
        pending_incidents = Incident.query.filter_by(author=current_user, status='En cours').count()
    
    return render_template('main_dashboard.html',
                         recent_incidents=recent_incidents,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         datetime=datetime)

@app.route('/dashboard')
@login_required
def dashboard():
    random_phrase = random.choice(WATER_PHRASES)
    
    # Get statistics
    if current_user.role == 'Admin':
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
        pending_incidents = Incident.query.filter_by(status='En cours').count()
    else:
        total_incidents = Incident.query.filter_by(author=current_user).count()
        resolved_incidents = Incident.query.filter_by(author=current_user, status='Résolu').count()
        pending_incidents = Incident.query.filter_by(author=current_user, status='En cours').count()
    
    # Get recent incidents (last 5)
    if current_user.role == 'Admin':
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
    else:
        recent_incidents = Incident.query.filter_by(author=current_user).order_by(Incident.date_incident.desc()).limit(5).all()
    
    return render_template('main_dashboard.html',
                         phrase=random_phrase,
                         datetime=datetime,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         recent_incidents=recent_incidents)

@app.route('/incidents')
@login_required
def incident_list():
    if current_user.role == 'Admin':
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
    else:
        incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).all()
    return render_template('incident_list.html', incidents=incidents)

@app.route('/incident/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    # Get all available units for admin, or just the user's unit for others
    if current_user.role == 'Admin':
        units = Unit.query.all()
    else:
        # If user is not admin and has no unit assigned
        if not current_user.unit_id:
            flash('Vous devez être assigné à une unité pour signaler un incident. Veuillez contacter votre administrateur.', 'warning')
            return redirect(url_for('dashboard'))
        units = [current_user.unit] if current_user.unit else []

    if request.method == 'POST':
        # For admin, use the selected unit_id from the form
        if current_user.role == 'Admin':
            unit_id = request.form.get('unit_id')
            if not unit_id:
                flash('Veuillez sélectionner une unité.', 'error')
                return render_template('new_incident.html', units=units)
        else:
            unit_id = current_user.unit_id

        try:
            incident = Incident(
                wilaya=request.form.get('wilaya'),
                commune=request.form.get('commune'),
                localite=request.form.get('localite'),
                nature_cause=request.form.get('nature_cause'),
                date_incident=datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M'),
                mesures_prises=request.form.get('mesures_prises'),
                impact=request.form.get('impact'),
                gravite=request.form.get('gravite').lower(),
                status='Nouveau',
                user_id=current_user.id,
                unit_id=unit_id
            )
            db.session.add(incident)
            db.session.commit()
            flash('Incident signalé avec succès', 'success')
            return redirect(url_for('incident_list'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de la création de l\'incident.', 'error')
            return render_template('new_incident.html', units=units)

    return render_template('new_incident.html', units=units)

@app.route('/update_unite', methods=['POST'])
@login_required
def update_unite():
    unite = request.form.get('unite')
    if unite in ['Unité de Blida', 'Unité de Boumerdes', 'Unité de Medea']:
        current_user.unite = unite
        db.session.commit()
        flash('Unité mise à jour avec succès', 'success')
    return redirect(request.referrer or url_for('incident_list'))

@app.route('/incident/<int:incident_id>')
@login_required
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and incident.author != current_user:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for('incident_list'))
    return render_template('view_incident.html', incident=incident)

@app.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and incident.author != current_user:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for('incident_list'))
    
    if request.method == 'POST':
        try:
            incident.wilaya = request.form.get('wilaya')
            incident.commune = request.form.get('commune')
            incident.localite = request.form.get('localite')
            incident.nature_cause = request.form.get('nature_cause')
            incident.date_incident = datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M')
            incident.mesures_prises = request.form.get('mesures_prises')
            incident.impact = request.form.get('impact')
            incident.gravite = request.form.get('gravite')
            
            db.session.commit()
            flash('Incident mis à jour avec succès.', 'success')
            return redirect(url_for('view_incident', incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de l\'incident: {str(e)}', 'danger')
            return render_template('edit_incident.html', incident=incident)
    
    return render_template('edit_incident.html', incident=incident)

@app.route('/delete_incident/<int:incident_id>', methods=['GET', 'POST'])
@login_required
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    
    # Check if user has permission to delete
    if not current_user.role == 'Admin' and incident.author != current_user:
        flash('Vous n\'avez pas la permission de supprimer cet incident.', 'danger')
        return redirect(url_for('incident_list'))
    
    try:
        db.session.delete(incident)
        db.session.commit()
        flash('Incident supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'incident: {str(e)}', 'danger')
    
    return redirect(url_for('incident_list'))

@app.route('/resolve_incident/<int:incident_id>', methods=['POST'])
@login_required
def resolve_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and incident.author != current_user:
        flash('Vous n\'êtes pas autorisé à résoudre cet incident.', 'danger')
        return redirect(url_for('incident_list'))
    
    if incident.status == 'Résolu':
        flash('Cet incident est déjà résolu.', 'warning')
        return redirect(url_for('incident_list'))
    
    mesures_prises = request.form.get('mesures_prises')
    if not mesures_prises:
        flash('Veuillez décrire les mesures prises pour résoudre l\'incident.', 'danger')
        return redirect(url_for('incident_list'))
    
    incident.status = 'Résolu'
    incident.mesures_prises = mesures_prises
    incident.date_resolution = datetime.now()
    db.session.commit()
    
    flash('L\'incident a été marqué comme résolu.', 'success')
    return redirect(url_for('incident_list'))

@app.route('/export_pdf/<int:incident_id>')
@login_required
def export_incident_pdf(incident_id):
    try:
        incident = Incident.query.get_or_404(incident_id)
        
        # Create temporary directory if it doesn't exist
        if not os.path.exists('temp'):
            os.makedirs('temp')
            
        # Generate PDF filename
        filename = f'incident_{incident.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join('temp', filename)
        
        # Get unit name safely
        unit_name = incident.unit.name if incident.unit else "Unité non spécifiée"
        
        # Generate PDF
        create_incident_pdf([incident], pdf_path, unit_name)
        
        # Send file to user and delete after sending
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'danger')
        return redirect(url_for('incident_list'))

@app.route('/export_all_pdf')
@login_required
def export_all_incidents_pdf():
    try:
        # Get all incidents based on user role
        if current_user.role == 'Admin':
            incidents = Incident.query.all()
        else:
            incidents = Incident.query.filter_by(unit_id=current_user.unit_id).all()
        
        if not incidents:
            flash('Aucun incident à exporter.', 'warning')
            return redirect(url_for('incident_list'))
        
        # Create temporary directory if it doesn't exist
        if not os.path.exists('temp'):
            os.makedirs('temp')
            
        # Generate PDF filename
        filename = f'all_incidents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join('temp', filename)
        
        # Get unit name safely
        unit_name = current_user.unit.name if current_user.unit else "Toutes les unités" if current_user.role == 'Admin' else "Unité non spécifiée"
        
        # Generate PDF
        create_incident_pdf(incidents, pdf_path, unit_name)
        
        # Send file to user
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'danger')
        return redirect(url_for('incident_list'))

@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route('/listes_dashboard')
@login_required
def listes_dashboard():
    if current_user.role == 'Admin':
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
    else:
        total_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).count()
        resolved_incidents = Incident.query.filter_by(unit_id=current_user.unit_id, status='Résolu').count()

    return render_template('listes_dashboard.html',
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents)

def is_admin():
    return current_user.is_authenticated and current_user.role == 'Admin'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Accès refusé. Seuls les administrateurs peuvent accéder à cette page.', 'danger')
            return redirect(url_for('main_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/units')
@login_required
@admin_required
def manage_units():
    units = Unit.query.all()
    return render_template('admin/manage_units.html', units=units)

@app.route('/admin/units/new', methods=['POST'])
@login_required
@admin_required
def new_unit():
    name = request.form.get('name')
    location = request.form.get('location')
    description = request.form.get('description')

    if not name:
        flash('Le nom de l\'unité est requis.', 'danger')
        return redirect(url_for('manage_units'))

    if Unit.query.filter_by(name=name).first():
        flash('Une unité avec ce nom existe déjà.', 'danger')
        return redirect(url_for('manage_units'))

    unit = Unit(name=name, location=location, description=description)
    db.session.add(unit)
    db.session.commit()
    flash('Unité créée avec succès.', 'success')
    return redirect(url_for('manage_units'))

@app.route('/admin/units/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    
    if request.method == 'GET':
        return jsonify({
            'name': unit.name,
            'location': unit.location or '',
            'description': unit.description or ''
        })

    name = request.form.get('name')
    location = request.form.get('location')
    description = request.form.get('description')

    if not name:
        flash('Le nom de l\'unité est requis.', 'danger')
        return redirect(url_for('manage_units'))

    existing_unit = Unit.query.filter_by(name=name).first()
    if existing_unit and existing_unit.id != unit_id:
        flash('Une unité avec ce nom existe déjà.', 'danger')
        return redirect(url_for('manage_units'))

    unit.name = name
    unit.location = location
    unit.description = description
    db.session.commit()
    flash('Unité mise à jour avec succès.', 'success')
    return redirect(url_for('manage_units'))

@app.route('/admin/units/<int:unit_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    
    if request.method == 'GET':
        if unit.users or unit.incidents:
            flash('Impossible de supprimer cette unité car elle contient des utilisateurs ou des incidents.', 'danger')
            return redirect(url_for('manage_units'))
        return render_template('admin/confirm_delete_unit.html', unit=unit)

    if unit.users or unit.incidents:
        flash('Impossible de supprimer cette unité car elle contient des utilisateurs ou des incidents.', 'danger')
        return redirect(url_for('manage_units'))

    db.session.delete(unit)
    db.session.commit()
    flash('Unité supprimée avec succès.', 'success')
    return redirect(url_for('manage_units'))

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    units = Unit.query.all()
    return render_template('admin/users.html', users=users, units=units)

@app.route('/admin/users/new', methods=['POST'])
@login_required
@admin_required
def new_user():
    username = request.form.get('username')
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    role = request.form.get('role')
    unit_id = request.form.get('unit_id')

    if User.query.filter_by(username=username).first():
        flash('Ce nom d\'utilisateur existe déjà.', 'danger')
        return redirect(url_for('manage_users'))

    user = User(username=username, nickname=nickname, role=role)
    if unit_id:
        user.unit_id = unit_id
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash('Utilisateur créé avec succès!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    role = request.form.get('role')
    unit_id = request.form.get('unit_id')

    if User.query.filter(User.username == username, User.id != user_id).first():
        flash('Ce nom d\'utilisateur existe déjà.', 'danger')
        return redirect(url_for('manage_users'))

    user.username = username
    user.nickname = nickname
    user.role = role
    if unit_id:
        user.unit_id = unit_id
    if password:
        user.set_password(password)

    db.session.commit()
    flash('Utilisateur modifié avec succès!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('manage_users'))

    user = User.query.get_or_404(user_id)
    if user.incidents:
        flash('Impossible de supprimer cet utilisateur car il a des incidents associés.', 'danger')
        return redirect(url_for('manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash('Utilisateur supprimé avec succès.', 'success')
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                role='Admin'
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
    
    print("\n" + "="*50)
    print("Application is running!")
    print("Default admin credentials:")
    print("Username: admin")
    print("Password: admin")
    print("Please change these credentials after first login.")
    print("="*50 + "\n")
    
    # Run the app
    app.run(host='127.0.0.1', port=8080, debug=True)
