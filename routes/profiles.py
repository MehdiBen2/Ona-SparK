from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, User, UserProfile, Unit
from datetime import datetime
from sqlalchemy import or_

profiles = Blueprint('profiles', __name__)

@profiles.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            date_of_birth = request.form.get('date_of_birth')
            email = request.form.get('email')
            professional_number = request.form.get('professional_number')
            job_function = request.form.get('job_function')
            recruitment_date = request.form.get('recruitment_date')

            # Validate required fields
            if not all([first_name, last_name, date_of_birth, email, professional_number, job_function, recruitment_date]):
                flash('Tous les champs sont obligatoires', 'error')
                return redirect(url_for('profiles.create_profile'))

            # Check if profile already exists
            if current_user.profile:
                flash('Le profil existe déjà', 'error')
                return redirect(url_for('profiles.view_profile'))

            # Check if professional number is already in use
            existing_profile = UserProfile.query.filter_by(professional_number=professional_number).first()
            if existing_profile:
                flash('Ce numéro professionnel est déjà utilisé', 'error')
                return render_template('profiles/create_profile.html', 
                                    form_data={
                                        'first_name': first_name,
                                        'last_name': last_name,
                                        'date_of_birth': date_of_birth,
                                        'email': email,
                                        'job_function': job_function,
                                        'recruitment_date': recruitment_date
                                    })

            # Create new profile
            profile = UserProfile(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date(),
                email=email,
                professional_number=professional_number,
                job_function=job_function,
                recruitment_date=datetime.strptime(recruitment_date, '%Y-%m-%d'),
                user_id=current_user.id
            )

            db.session.add(profile)
            db.session.commit()
            flash('Profil créé avec succès', 'success')
            return redirect(url_for('profiles.view_profile'))

        except Exception as e:
            db.session.rollback()
            print("Erreur lors de la création du profil:", str(e))
            if 'UNIQUE constraint failed: user_profile.email' in str(e):
                flash('Cette adresse email est déjà utilisée', 'error')
            elif 'UNIQUE constraint failed: user_profile.professional_number' in str(e):
                flash('Ce numéro professionnel est déjà utilisé', 'error')
            else:
                flash(f'Erreur lors de la création du profil: {str(e)}', 'error')
            
            return render_template('profiles/create_profile.html',
                                form_data={
                                    'first_name': request.form.get('first_name'),
                                    'last_name': request.form.get('last_name'),
                                    'date_of_birth': request.form.get('date_of_birth'),
                                    'email': request.form.get('email'),
                                    'job_function': request.form.get('job_function'),
                                    'recruitment_date': request.form.get('recruitment_date')
                                })

    return render_template('profiles/create_profile.html', form_data={})

@profiles.route('/profile', methods=['GET'])
@login_required
def view_profile():
    if not current_user.profile:
        flash('Vous n\'avez pas encore créé votre profil.', 'info')
        return redirect(url_for('profiles.create_profile'))
    
    return render_template('profiles/view_profile.html', profile=current_user.profile)

@profiles.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def view_user_profile(user_id):
    # Check if the current user is an admin or viewing their own profile
    if not current_user.role == 'Admin' and current_user.id != user_id:
        flash('Vous n\'avez pas la permission de voir ce profil.', 'error')
        return redirect(url_for('profiles.view_profile'))
    
    user = User.query.get_or_404(user_id)
    if not user.profile:
        flash('Ce utilisateur n\'a pas encore créé son profil.', 'info')
        return redirect(url_for('profiles.admin_profiles'))
    
    return render_template('profiles/view_profile.html', profile=user.profile, is_admin_view=True)

@profiles.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('profiles.create_profile'))

    if request.method == 'POST':
        try:
            profile.first_name = request.form.get('first_name')
            profile.last_name = request.form.get('last_name')
            profile.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            profile.email = request.form.get('email')
            profile.professional_number = request.form.get('professional_number')
            profile.job_function = request.form.get('job_function')
            profile.recruitment_date = datetime.strptime(request.form.get('recruitment_date'), '%Y-%m-%d')

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profiles.view_profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')

    return render_template('profiles/edit_profile.html', profile=profile)

@profiles.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user_profile(user_id):
    if current_user.role != 'Admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    profile = user.profile
    
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('profiles.admin_profiles'))

    if request.method == 'POST':
        try:
            profile.first_name = request.form.get('first_name')
            profile.last_name = request.form.get('last_name')
            profile.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            profile.email = request.form.get('email')
            profile.professional_number = request.form.get('professional_number')
            profile.job_function = request.form.get('job_function')
            profile.recruitment_date = datetime.strptime(request.form.get('recruitment_date'), '%Y-%m-%d')

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profiles.view_user_profile', user_id=user_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')

    return render_template('profiles/edit_profile.html', profile=profile, is_admin_view=True)

@profiles.route('/admin/profiles', methods=['GET'])
@login_required
def admin_profiles():
    if current_user.role != 'Admin':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('index'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'last_name')
    order = request.args.get('order', 'asc')

    query = UserProfile.query
    
    if search_query:
        query = query.join(User).join(Unit).filter(
            or_(
                UserProfile.first_name.ilike(f'%{search_query}%'),
                UserProfile.last_name.ilike(f'%{search_query}%'),
                UserProfile.email.ilike(f'%{search_query}%'),
                UserProfile.professional_number.ilike(f'%{search_query}%'),
                Unit.name.ilike(f'%{search_query}%')
            )
        )

    if hasattr(UserProfile, sort_by):
        sort_column = getattr(UserProfile, sort_by)
        if order == 'desc':
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

    profiles = query.all()
    return render_template('profiles/admin_profiles.html', profiles=profiles)

@profiles.route('/api/profiles/search', methods=['GET'])
@login_required
def search_profiles():
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    search_query = request.args.get('q', '')
    profiles = UserProfile.query.join(User).join(Unit).filter(
        or_(
            UserProfile.first_name.ilike(f'%{search_query}%'),
            UserProfile.last_name.ilike(f'%{search_query}%'),
            UserProfile.email.ilike(f'%{search_query}%'),
            UserProfile.professional_number.ilike(f'%{search_query}%'),
            Unit.name.ilike(f'%{search_query}%')
        )
    ).all()

    return jsonify([{
        'id': p.id,
        'first_name': p.first_name,
        'last_name': p.last_name,
        'email': p.email,
        'professional_number': p.professional_number,
        'unit': p.user.unit.name if p.user.unit else None
    } for p in profiles])
