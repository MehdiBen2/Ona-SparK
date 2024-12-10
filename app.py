from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
from io import BytesIO
import pandas as pd
import random
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from models import db, User, Unit, Incident, Zone, Center
from routes.auth import auth
from routes.profiles import profiles
from flask.cli import with_appcontext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ona_incidents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# Configure session for Railway
if os.getenv('RAILWAY_ENVIRONMENT'):
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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

@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database."""
    from scripts.init_db import init_database
    init_database()
    click.echo('Initialized the database.')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('Vous devez être administrateur pour accéder à cette page.', 'danger')
            return redirect(url_for('incident_list'))
        return f(*args, **kwargs)
    return decorated_function

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
    print(f"Debug - Starting dashboard route")
    print(f"Debug - Current user: {current_user.username}, Role: {current_user.role}")
    
    random_phrase = random.choice(WATER_PHRASES)
    
    with app.app_context():
        # Get counts for dashboard statistics
        try:
            users_count = User.query.count()
            print(f"Debug - Users count: {users_count}")
            units_count = Unit.query.count()
            print(f"Debug - Units count: {units_count}")
            zones_count = Zone.query.count()
            print(f"Debug - Zones count: {zones_count}")
            centers_count = Center.query.count()
            print(f"Debug - Centers count: {centers_count}")
        except Exception as e:
            print(f"Debug - Error getting counts: {str(e)}")
            users_count = units_count = zones_count = centers_count = 0

        # Get statistics
        if current_user.role == 'Admin' or current_user.role == 'Employeur DG':
            print("Debug - User is Admin or Employeur DG")
            total_incidents = Incident.query.count()
            resolved_incidents = Incident.query.filter_by(status='Résolu').count()
            pending_incidents = Incident.query.filter_by(status='En cours').count()
            recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
        else:
            print("Debug - User is not Admin")
            if current_user.assigned_unit is None:
                total_incidents = 0
                resolved_incidents = 0
                pending_incidents = 0
                recent_incidents = []
                flash('Vous n\'avez pas d\'unité assignée. Veuillez contacter l\'administrateur.', 'warning')
            else:
                total_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id).count()
                resolved_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id, status='Résolu').count()
                pending_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id, status='En cours').count()
                recent_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id).order_by(Incident.date_incident.desc()).limit(5).all()
    
    print(f"Debug - About to render template with counts: users={users_count}, units={units_count}, zones={zones_count}, centers={centers_count}")
    return render_template('main_dashboard.html',
                         random_phrase=random_phrase,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         recent_incidents=recent_incidents,
                         users_count=users_count,
                         units_count=units_count,
                         zones_count=zones_count,
                         centers_count=centers_count,
                         datetime=datetime)

@app.route('/incidents')
@login_required
def incident_list():
    if current_user.role == 'Admin' or current_user.role == 'Employeur DG':
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
    else:
        if current_user.assigned_unit is None:
            flash('Vous n\'avez pas d\'unité assignée. Veuillez contacter l\'administrateur.', 'warning')
            incidents = []
        else:
            incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id).order_by(Incident.date_incident.desc()).all()
    
    return render_template('incident_list.html', incidents=incidents)

@app.route('/incident/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    # Get all available units for admin, or just the user's unit for others
    if current_user.role == 'Admin':
        units = Unit.query.all()
    else:
        # If user is not admin and has no unit assigned
        if not current_user.assigned_unit:
            flash('Vous devez être assigné à une unité pour signaler un incident. Veuillez contacter votre administrateur.', 'warning')
            return redirect(url_for('dashboard'))
        units = [current_user.assigned_unit] if current_user.assigned_unit else []

    if request.method == 'POST':
        try:
            # For admin, use the selected unit_id from the form
            if current_user.role == 'Admin':
                unit_id = request.form.get('unit_id')
                if not unit_id:
                    flash('Veuillez sélectionner une unité.', 'error')
                    return render_template('new_incident.html', units=units)
            else:
                unit_id = current_user.assigned_unit.id

            # Generate a title based on the nature and location
            title = f"Incident - {request.form.get('nature_cause')[:50]} à {request.form.get('commune')}"
            
            incident = Incident(
                title=title,
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
        except ValueError as e:
            db.session.rollback()
            flash(f'Erreur de format de données: {str(e)}', 'error')
            return render_template('new_incident.html', units=units)
        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue lors de la création de l\'incident: {str(e)}', 'error')
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
    if not current_user.role == 'Admin' and current_user.assigned_unit.id != incident.unit_id:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for('incident_list'))
    return render_template('view_incident.html', incident=incident)

@app.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and current_user.assigned_unit.id != incident.unit_id:
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
    if not current_user.role == 'Admin' and current_user.assigned_unit.id != incident.unit_id:
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
    if not current_user.role == 'Admin' and current_user.assigned_unit.id != incident.unit_id:
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
            incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id).all()
        
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
        unit_name = current_user.assigned_unit.name if current_user.assigned_unit else "Toutes les unités" if current_user.role == 'Admin' else "Unité non spécifiée"
        
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
        total_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id).count()
        resolved_incidents = Incident.query.filter_by(unit_id=current_user.assigned_unit.id, status='Résolu').count()

    return render_template('listes_dashboard.html',
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents)

@app.route('/merge_incident/<int:incident_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def merge_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    units = Unit.query.filter(Unit.id != incident.unit_id).all()
    
    if request.method == 'POST':
        new_unit_id = request.form.get('new_unit')
        merge_note = request.form.get('merge_note')
        
        if not new_unit_id:
            flash('Veuillez sélectionner une unité de destination.', 'danger')
            return redirect(url_for('merge_incident', incident_id=incident_id))
            
        try:
            # Update the incident's unit
            new_unit = Unit.query.get(new_unit_id)
            old_unit_name = incident.unit.name if incident.unit else "Unité non spécifiée"
            
            incident.unit_id = new_unit_id
            
            # Add merge note to mesures_prises if provided
            if merge_note:
                merge_info = f"\n\n[Fusion d'unité le {datetime.now().strftime('%d/%m/%Y %H:%M')}]\n"
                merge_info += f"Transféré de l'unité '{old_unit_name}' vers '{new_unit.name}'\n"
                merge_info += f"Note: {merge_note}"
                
                if incident.mesures_prises:
                    incident.mesures_prises += merge_info
                else:
                    incident.mesures_prises = merge_info
            
            db.session.commit()
            flash(f'L\'incident a été fusionné avec succès vers l\'unité {new_unit.name}.', 'success')
            return redirect(url_for('view_incident', incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion de l\'incident: {str(e)}', 'danger')
            return redirect(url_for('merge_incident', incident_id=incident_id))
    
    return render_template('merge_incident.html', incident=incident, units=units)

@app.route('/batch_merge', methods=['GET', 'POST'])
@login_required
@admin_required
def batch_merge():
    units = Unit.query.all()
    
    if request.method == 'POST':
        source_unit_id = request.form.get('source_unit')
        target_unit_id = request.form.get('target_unit')
        incident_ids = request.form.getlist('incidents')
        merge_note = request.form.get('merge_note')
        
        if not all([source_unit_id, target_unit_id, incident_ids]):
            flash('Veuillez sélectionner les unités source et destination et au moins un incident.', 'danger')
            return redirect(url_for('batch_merge'))
            
        try:
            source_unit = Unit.query.get(source_unit_id)
            target_unit = Unit.query.get(target_unit_id)
            
            # Add merge note
            merge_info = f"\n\n[Fusion en lot le {datetime.now().strftime('%d/%m/%Y %H:%M')}]\n"
            merge_info += f"Transféré de l'unité '{source_unit.name}' vers '{target_unit.name}'\n"
            if merge_note:
                merge_info += f"Note: {merge_note}"
            
            # Update all selected incidents
            for incident_id in incident_ids:
                incident = Incident.query.get(incident_id)
                if incident and incident.unit_id == int(source_unit_id):
                    incident.unit_id = target_unit_id
                    if incident.mesures_prises:
                        incident.mesures_prises += merge_info
                    else:
                        incident.mesures_prises = merge_info
            
            db.session.commit()
            flash(f'{len(incident_ids)} incidents ont été fusionnés avec succès vers l\'unité {target_unit.name}.', 'success')
            return redirect(url_for('incident_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion des incidents: {str(e)}', 'danger')
            return redirect(url_for('batch_merge'))
    
    return render_template('batch_merge.html', units=units)

@app.route('/get_unit_incidents/<int:unit_id>')
@login_required
@admin_required
def get_unit_incidents(unit_id):
    incidents = Incident.query.filter_by(unit_id=unit_id).order_by(Incident.date_incident.desc()).all()
    return jsonify([{
        'id': incident.id,
        'localite': incident.localite,
        'nature_cause': incident.nature_cause,
        'date_incident': incident.date_incident.strftime('%d/%m/%Y %H:%M')
    } for incident in incidents])

@app.route('/departement')
@login_required
def departement():
    return render_template('departement.html')

@app.route('/exploitation')
@login_required
def exploitation():
    return render_template('departement/exploitation.html')

@app.route('/rapports')
@login_required
def rapports():
    return render_template('departement/rapports.html')

def is_admin():
    return current_user.is_authenticated and current_user.role == 'Admin'

@app.route('/admin/units')
@login_required
@admin_required
def manage_units():
    units = Unit.query.all()
    zones = Zone.query.all()
    print("DEBUG - Number of zones:", len(zones))
    for zone in zones:
        print(f"DEBUG - Zone: {zone.name} (ID: {zone.id})")
    return render_template('admin/manage_units.html', units=units, zones=zones)

@app.route('/admin/units/new', methods=['POST'])
@login_required
@admin_required
def new_unit():
    name = request.form.get('name')
    address = request.form.get('address')
    description = request.form.get('description')
    zone_id = request.form.get('zone_id')

    if not name or not zone_id:
        flash('Le nom et la zone sont requis.', 'danger')
        return redirect(url_for('manage_units'))

    try:
        unit = Unit(
            name=name,
            address=address,
            description=description,
            zone_id=zone_id
        )
        db.session.add(unit)
        db.session.commit()
        flash('Unité créée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création de l\'unité: {str(e)}', 'danger')

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
    
    # Check if unit has associated users or incidents
    if unit.unit_users or unit.incidents:
        flash('Impossible de supprimer cette unité car elle a des utilisateurs ou des incidents associés.', 'danger')
        return redirect(url_for('manage_units'))

    if request.method == 'GET':
        return render_template('admin/confirm_delete_unit.html', unit=unit)

    try:
        db.session.delete(unit)
        db.session.commit()
        flash('Unité supprimée avec succès!', 'success')
        return redirect(url_for('manage_units'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'unité: {str(e)}', 'danger')
        return redirect(url_for('manage_units'))

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    # Get all users with their related unit and zone information using explicit join conditions
    users = User.query\
        .outerjoin(Unit, User.unit_id == Unit.id)\
        .outerjoin(Zone, (User.zone_id == Zone.id) | (Unit.zone_id == Zone.id))\
        .all()
    units = Unit.query.all()
    zones = Zone.query.all()
    return render_template('admin/users.html', users=users, units=units, zones=zones)

@app.route('/get_units_by_zone/<int:zone_id>')
@login_required
def get_units_by_zone(zone_id):
    """Get all units for a specific zone."""
    try:
        units = Unit.query.filter_by(zone_id=zone_id).all()
        return jsonify([{'id': unit.id, 'name': unit.name} for unit in units])
    except Exception as e:
        app.logger.error(f"Error fetching units for zone {zone_id}: {str(e)}")
        return jsonify({'error': 'Error fetching units'}), 500

@app.route('/manage_users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if current_user.role != 'Admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        role = request.form.get('role')
        unit_id = request.form.get('unit_id')
        zone_id = request.form.get('zone_id')

        print(f"Debug - Received form data: role={role}, unit_id={unit_id}, zone_id={zone_id}")  # Debug log

        if not username or not password or not role or not nickname:
            flash('Tous les champs obligatoires doivent être remplis.', 'danger')
            return redirect(url_for('manage_users'))

        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('manage_users'))

        try:
            # Normalize role names
            role_mapping = {
                'Admin': 'Admin',
                'Employeur DG': 'Employeur DG',
                'Employeur de Zone': 'Employeur de Zone',
                'Employeur de l\'unité': 'Employeur de l\'unité'
            }
            normalized_role = role_mapping.get(role)
            if not normalized_role:
                flash('Rôle invalide sélectionné.', 'danger')
                return redirect(url_for('manage_users'))

            new_user = User(
                username=username,
                nickname=nickname,
                role=normalized_role
            )
            new_user.set_password(password)

            # Handle unit and zone assignments based on role
            if normalized_role == 'Employeur de Zone':
                if not zone_id:
                    flash('Une zone doit être sélectionnée pour un Employeur de Zone.', 'danger')
                    return redirect(url_for('manage_users'))
                new_user.zone_id = zone_id
            elif normalized_role == 'Employeur de l\'unité':
                if not unit_id:
                    flash('Une unité doit être sélectionnée pour un Employeur de l\'unité.', 'danger')
                    return redirect(url_for('manage_users'))
                new_user.unit_id = unit_id
                unit = Unit.query.get(unit_id)
                if unit:
                    new_user.zone_id = unit.zone_id

            db.session.add(new_user)
            db.session.commit()
            flash('Utilisateur créé avec succès!', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            print(f"Debug - Error creating user: {str(e)}")  # Debug log
            flash(f'Erreur lors de la création de l\'utilisateur: {str(e)}', 'danger')
            return redirect(url_for('manage_users'))

    # GET request - show the form
    zones = Zone.query.all()
    units = Unit.query.all()
    return render_template('admin/create_user.html', zones=zones, units=units)

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    nickname = request.form.get('nickname')
    unit_id = request.form.get('unit_id')
    zone_id = request.form.get('zone_id')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user_id:
        flash('Un utilisateur avec ce nom existe déjà.', 'error')
        return redirect(url_for('manage_users'))

    user.username = username
    user.role = role
    if password:
        user.set_password(password)
    if nickname:
        user.nickname = nickname
    else:
        user.nickname = None
    user.unit_id = unit_id

    db.session.commit()
    flash('Utilisateur mis à jour avec succès.', 'success')
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

@app.route('/zones')
@login_required
def list_zones():
    zones = Zone.query.all()
    return render_template('admin/zones.html', zones=zones)

@app.route('/centers')
@login_required
def list_centers():
    # If user is admin, show all centers
    if current_user.role == 'Admin':
        centers = Center.query.all()
        zones = Zone.query.all()
    # If user is Unit Officer, show only centers in their unit
    elif current_user.assigned_unit:
        centers = Center.query.filter_by(unit_id=current_user.assigned_unit.id).all()
        zones = []
    else:
        centers = []
        zones = []
    return render_template('admin/centers.html', centers=centers, zones=zones)

@app.route('/zones/create', methods=['POST'])
@login_required
def create_zone():
    if current_user.role != 'Admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    try:
        zone = Zone(
            code=request.form['code'],
            name=request.form['name'],
            description=request.form['description'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(zone)
        db.session.commit()
        flash('Zone créée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création de la zone: {str(e)}', 'danger')
    
    return redirect(url_for('list_zones'))

@app.route('/zones/edit/<int:id>', methods=['POST'])
@login_required
def edit_zone(id):
    if current_user.role != 'Admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    zone = Zone.query.get_or_404(id)
    try:
        zone.code = request.form['code']
        zone.name = request.form['name']
        zone.description = request.form['description']
        zone.address = request.form['address']
        zone.phone = request.form['phone']
        zone.email = request.form['email']
        db.session.commit()
        flash('Zone mise à jour avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour de la zone: {str(e)}', 'danger')
    
    return redirect(url_for('list_zones'))

@app.route('/zones/delete/<int:id>', methods=['POST'])
@login_required
def delete_zone(id):
    if current_user.role != 'Admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    try:
        zone = Zone.query.get_or_404(id)
        
        # Delete all units in the zone first
        for unit in zone.units:
            # Delete all centers in each unit
            for center in unit.centers:
                db.session.delete(center)
            db.session.delete(unit)
        
        # Finally delete the zone
        db.session.delete(zone)
        db.session.commit()
        flash('Zone supprimée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la zone: {str(e)}', 'danger')
    
    return redirect(url_for('list_zones'))

@app.route('/centers/create', methods=['POST'])
@login_required
def create_center():
    if current_user.role not in ['Admin', 'Unit Officer']:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    try:
        # If Unit Officer, use their unit_id
        unit_id = current_user.assigned_unit.id if current_user.role == 'Unit Officer' else request.form['unit_id']
        
        center = Center(
            name=request.form['name'],
            description=request.form['description'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email'],
            unit_id=unit_id
        )
        db.session.add(center)
        db.session.commit()
        flash('Centre créé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création du centre: {str(e)}', 'danger')
    
    return redirect(url_for('list_centers'))

@app.route('/centers/edit/<int:id>', methods=['POST'])
@login_required
def edit_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'Unit Officer' and center.unit_id != current_user.assigned_unit.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    try:
        center.name = request.form['name']
        center.description = request.form['description']
        center.address = request.form['address']
        center.phone = request.form['phone']
        center.email = request.form['email']
        if current_user.role == 'Admin':
            center.unit_id = request.form['unit_id']
        db.session.commit()
        flash('Centre mis à jour avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour du centre: {str(e)}', 'danger')
    
    return redirect(url_for('list_centers'))

@app.route('/centers/delete/<int:id>', methods=['POST'])
@login_required
def delete_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'Unit Officer' and center.unit_id != current_user.assigned_unit.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    
    try:
        db.session.delete(center)
        db.session.commit()
        flash('Centre supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du centre: {str(e)}', 'danger')
    
    return redirect(url_for('list_centers'))

@app.route('/units')
@login_required
def list_units():
    if current_user.role != 'Admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard'))
    units = Unit.query.all()
    return render_template('admin/units.html', units=units)

@app.route('/api/dashboard-stats')
@login_required
def get_dashboard_stats():
    try:
        if current_user.role in ['Admin', 'Employeur DG']:
            # Get admin stats
            users_count = User.query.count()
            units_count = Unit.query.count()
            zones_count = Zone.query.count()
            centers_count = Center.query.count()
            
            return jsonify({
                'success': True,
                'data': {
                    'users_count': users_count,
                    'units_count': units_count,
                    'zones_count': zones_count,
                    'centers_count': centers_count
                }
            })
        else:
            # Get user stats
            if current_user.unit_id:
                total_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).count()
                resolved_incidents = Incident.query.filter_by(
                    unit_id=current_user.unit_id,
                    status='Résolu'
                ).count()
                pending_incidents = total_incidents - resolved_incidents
            else:
                total_incidents = 0
                resolved_incidents = 0
                pending_incidents = 0
            
            return jsonify({
                'success': True,
                'data': {
                    'total_incidents': total_incidents,
                    'resolved_incidents': resolved_incidents,
                    'pending_incidents': pending_incidents
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/create_incident', methods=['GET', 'POST'])
@login_required
def create_incident():
    if request.method == 'POST':
        # Handle form submission
        pass
    return render_template('create_incident.html')

@app.route('/incident_stats')
@login_required
def incident_stats():
    # Get incident statistics
    total_incidents = Incident.query.count()
    resolved_incidents = Incident.query.filter_by(status='Résolu').count()
    pending_incidents = total_incidents - resolved_incidents

    return render_template('incident_stats.html', 
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents)

if __name__ == '__main__':
    # Create default admin user if it doesn't exist
    with app.app_context():
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
    app.run(debug=True, host='0.0.0.0', port=5000)
