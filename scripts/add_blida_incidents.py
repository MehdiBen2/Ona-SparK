from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Incident, Unit, User

# Sample incident data for Blida
blida_incidents = [
    {
        "wilaya": "Blida",
        "commune": "Boufarik",
        "localite": "Centre Ville",
        "nature_cause": "Débordement du réseau d'assainissement",
        "date_incident": datetime.now() - timedelta(days=5),
        "mesures_prises": "Intervention immédiate de l'équipe d'entretien. Nettoyage et débouchage du réseau effectués.",
        "impact": "Perturbation temporaire de la circulation et désagrément pour les riverains",
        "gravite": "moyenne",
        "status": "Résolu"
    },
    {
        "wilaya": "Blida",
        "commune": "Beni Mered",
        "localite": "Quartier El Fath",
        "nature_cause": "Rupture de la conduite principale",
        "date_incident": datetime.now() - timedelta(days=3),
        "mesures_prises": "Remplacement de la section endommagée et renforcement du réseau",
        "impact": "Coupure temporaire du service d'assainissement pour 200 foyers",
        "gravite": "haute",
        "status": "Résolu"
    },
    {
        "wilaya": "Blida",
        "commune": "Ouled Yaich",
        "localite": "Zone Industrielle",
        "nature_cause": "Pollution industrielle",
        "date_incident": datetime.now() - timedelta(days=1),
        "mesures_prises": "Prélèvement d'échantillons et notification des services environnementaux",
        "impact": "Risque de contamination des eaux souterraines",
        "gravite": "haute",
        "status": "En cours"
    },
    {
        "wilaya": "Blida",
        "commune": "Blida",
        "localite": "Cité Ben Boulaid",
        "nature_cause": "Effondrement partiel du collecteur",
        "date_incident": datetime.now() - timedelta(hours=12),
        "mesures_prises": "Mise en place d'une déviation temporaire et début des travaux de réparation",
        "impact": "Perturbation du trafic routier",
        "gravite": "moyenne",
        "status": "En cours"
    },
    {
        "wilaya": "Blida",
        "commune": "Chebli",
        "localite": "Route Nationale",
        "nature_cause": "Obstruction majeure du réseau",
        "date_incident": datetime.now() - timedelta(days=2),
        "mesures_prises": "Utilisation d'équipement spécialisé pour le débouchage",
        "impact": "Ralentissement de la circulation",
        "gravite": "basse",
        "status": "Résolu"
    }
]

def add_blida_incidents():
    with app.app_context():
        # Print all units and users for debugging
        print("\nAll Units:")
        for unit in Unit.query.all():
            print(f"ID: {unit.id}, Name: {unit.name}")
        
        print("\nAll Users:")
        for user in User.query.all():
            print(f"ID: {user.id}, Username: {user.username}, Unit ID: {user.unit_id}")

        # Get the Blida unit by ID
        blida_unit = Unit.query.get(3)
        if not blida_unit:
            print("Error: Unit with ID 3 not found")
            return

        # Get user with ID 3
        blida_user = User.query.get(3)
        if not blida_user:
            print("Error: User with ID 3 not found")
            return

        # Add each incident
        for incident_data in blida_incidents:
            incident = Incident(
                wilaya=incident_data["wilaya"],
                commune=incident_data["commune"],
                localite=incident_data["localite"],
                nature_cause=incident_data["nature_cause"],
                date_incident=incident_data["date_incident"],
                mesures_prises=incident_data["mesures_prises"],
                impact=incident_data["impact"],
                gravite=incident_data["gravite"],
                status=incident_data["status"],
                user_id=blida_user.id,
                unit_id=blida_unit.id
            )
            db.session.add(incident)

        try:
            db.session.commit()
            print(f"Successfully added {len(blida_incidents)} incidents for Unité de Blida")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding incidents: {str(e)}")

if __name__ == "__main__":
    add_blida_incidents()
