from app import app, db
from models import User, Zone, Unit
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default zone if it doesn't exist
        default_zone = Zone.query.filter_by(name='Zone 1').first()
        if not default_zone:
            default_zone = Zone(
                name='Zone 1',
                description='Default Zone'
            )
            db.session.add(default_zone)
            db.session.commit()
            print("Default zone created successfully!")

        # Create default unit if it doesn't exist
        default_unit = Unit.query.filter_by(name='Unit 1').first()
        if not default_unit:
            default_unit = Unit(
                name='Unit 1',
                description='Default Unit',
                zone_id=default_zone.id
            )
            db.session.add(default_unit)
            db.session.commit()
            print("Default unit created successfully!")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create admin user with unit and zone
            admin = User(
                username='admin',
                nickname='Administrator',
                email='admin@example.com',
                password_hash=generate_password_hash('admin'),
                role='admin',
                is_active=True,
                unit_id=default_unit.id,
                zone_id=default_zone.id
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            # Update existing admin user with unit and zone if needed
            if not admin_user.unit_id or not admin_user.zone_id:
                admin_user.unit_id = default_unit.id
                admin_user.zone_id = default_zone.id
                db.session.commit()
                print("Updated admin user with unit and zone!")

if __name__ == '__main__':
    init_db()
