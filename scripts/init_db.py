from datetime import datetime
import sys
import os
from werkzeug.security import generate_password_hash

# Add the parent directory to the Python path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Unit, User, Zone, Center

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Create directors first
        directors_data = [
            {
                "username": "D_zone_alger",
                "password": "alger123",
                "email": "directeur.alger@ona.dz",
                "role": "Directeur de Zone",
                "unit_id": None  # Zone director doesn't belong to a unit
            },
            {
                "username": "D_unite_medea",
                "password": "medea123",
                "email": "directeur.medea@ona.dz",
                "role": "Directeur d'Unité",
                "unit_id": None  # Will be set after unit creation
            },
            {
                "username": "D_unite_blida",
                "password": "blida123",
                "email": "directeur.blida@ona.dz",
                "role": "Directeur d'Unité",
                "unit_id": None
            },
            {
                "username": "D_unite_boumerdes",
                "password": "boumerdes123",
                "email": "directeur.boumerdes@ona.dz",
                "role": "Directeur d'Unité",
                "unit_id": None
            }
        ]

        # Create directors
        directors = {}
        for director_info in directors_data:
            user = User.query.filter_by(username=director_info["username"]).first()
            if not user:
                password = director_info.pop("password")
                user = User(**director_info)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                print(f"Created director: {user.username}")
            directors[director_info["username"]] = user
            print(f"Director exists: {user.username}")

        # Create Zone if it doesn't exist
        zone = Zone.query.filter_by(code="ALG").first()
        if not zone:
            # Check if a zone with this email exists
            existing_zone = Zone.query.filter_by(email="zone.alger@ona.dz").first()
            if existing_zone:
                zone = existing_zone
                print("Using existing zone with email: zone.alger@ona.dz")
            else:
                zone = Zone(
                    name="Zone d'Alger",
                    code="ALG",
                    email="zone.alger@ona.dz",
                    phone="+213 23 45 67 89",
                    description="Zone d'Alger regroupant les unités de Medea, Blida et Boumerdes",
                    director_id=directors["D_zone_alger"].id
                )
                db.session.add(zone)
                try:
                    db.session.commit()
                    print("Created zone: Zone d'Alger")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating zone: {str(e)}")
                    zone = Zone.query.filter_by(email="zone.alger@ona.dz").first()
                    if not zone:
                        raise e
        else:
            print("Zone already exists: Zone d'Alger")

        # Create Units if they don't exist
        units_data = [
            {
                "name": "Unité de Medea",
                "code": "MED",
                "email": "unite.medea@ona.dz",
                "phone": "+213 25 45 67 89",
                "description": "Unité de Medea",
                "zone_id": zone.id,
                "director_username": "D_unite_medea"
            },
            {
                "name": "Unité de Blida",
                "code": "BLD",
                "email": "unite.blida@ona.dz",
                "phone": "+213 25 58 67 89",
                "description": "Unité de Blida",
                "zone_id": zone.id,
                "director_username": "D_unite_blida"
            },
            {
                "name": "Unité de Boumerdes",
                "code": "BUM",
                "email": "unite.boumerdes@ona.dz",
                "phone": "+213 24 45 67 89",
                "description": "Unité de Boumerdes",
                "zone_id": zone.id,
                "director_username": "D_unite_boumerdes"
            }
        ]

        # Create units and assign directors
        for unit_info in units_data:
            director_username = unit_info.pop("director_username")
            unit = Unit.query.filter_by(code=unit_info["code"]).first()
            if not unit:
                director = directors[director_username]
                unit = Unit(**unit_info, director_id=director.id)
                db.session.add(unit)
                director.unit_id = unit.id  # Update director's unit
                db.session.commit()
                print(f"Created unit: {unit.name}")
            else:
                print(f"Unit already exists: {unit.name}")

        # Create users if they don't exist
        users_data = [
            {
                "username": "U_blida",
                "password": "blida",
                "email": "u_blida@ona.dz",
                "role": "Employeur",
                "unit_id": Unit.query.filter_by(code="BLD").first().id
            },
            {
                "username": "U_medea",
                "password": "medea",
                "email": "u_medea@ona.dz",
                "role": "Employeur",
                "unit_id": Unit.query.filter_by(code="MED").first().id
            },
            {
                "username": "U_boumerdes",
                "password": "boumerdes",
                "email": "u_boumerdes@ona.dz",
                "role": "Employeur",
                "unit_id": Unit.query.filter_by(code="BUM").first().id
            }
        ]

        # Create or update users
        for user_info in users_data:
            try:
                user = User.query.filter_by(username=user_info["username"]).first()
                if not user:
                    # Hash the password before creating the user
                    password = user_info.pop("password")
                    user = User(
                        username=user_info["username"],
                        email=user_info["email"],
                        role=user_info["role"],
                        unit_id=user_info["unit_id"]
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    print(f"Created user: {user.username}")
                else:
                    print(f"User already exists: {user.username}")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating user: {str(e)}")

if __name__ == "__main__":
    init_database()
