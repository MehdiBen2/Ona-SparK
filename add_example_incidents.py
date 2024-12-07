from app import app, db
from models import Unit, User, Incident
from datetime import datetime, timedelta
import random

def create_example_incidents():
    with app.app_context():
        # Get the Blida unit and a user from that unit
        blida_unit = Unit.query.filter_by(name='Unité de Blida').first()
        if not blida_unit:
            print("Error: Unité de Blida not found")
            return
        
        blida_user = User.query.filter_by(unit_id=blida_unit.id).first()
        if not blida_user:
            print("Error: No user found for Unité de Blida")
            return

        # Example data
        communes_blida = ['Blida', 'Boufarik', 'Bougara', 'Mouzaia', 'Oued El Alleug']
        localites = ['Station de relevage principale', 'Station d\'épuration', 'Réseau principal', 'Station de pompage', 'Bassin de rétention']
        natures = [
            'Panne de la pompe principale due à une surcharge',
            'Obstruction majeure dans le système de filtration',
            'Défaillance du système électrique',
            'Fuite importante sur la conduite principale',
            'Dysfonctionnement du système de chloration',
            'Problème de régulation du débit',
            'Panne du système d\'aération',
            'Défaut d\'étanchéité du bassin',
            'Dysfonctionnement des vannes automatiques',
            'Panne du système de contrôle automatisé'
        ]
        impacts = [
            'Perturbation temporaire du service d\'assainissement',
            'Risque de débordement dans les zones basses',
            'Réduction de la capacité de traitement',
            'Impact sur la qualité du traitement',
            'Arrêt partiel des opérations de pompage',
            'Ralentissement du processus d\'épuration',
            'Risque environnemental modéré',
            'Surcharge temporaire du réseau',
            'Diminution de l\'efficacité du traitement',
            'Perturbation du cycle de traitement'
        ]
        mesures = [
            'Intervention immédiate de l\'équipe technique',
            'Mise en place d\'une solution de pompage temporaire',
            'Réparation d\'urgence effectuée',
            'Nettoyage et maintenance corrective',
            'Remplacement des pièces défectueuses',
            'Activation du système de secours',
            'Réparation programmée avec bypass temporaire',
            'Intervention des équipes spécialisées',
            'Maintenance préventive renforcée',
            'Installation d\'équipements de rechange'
        ]
        gravites = ['Critique', 'Élevée', 'Moyenne', 'Faible']
        statuts = ['Nouveau', 'En cours', 'Résolu']

        # Create 10 incidents
        for i in range(10):
            # Calculate a random date within the last 30 days
            days_ago = random.randint(0, 30)
            incident_date = datetime.now() - timedelta(days=days_ago, 
                                                     hours=random.randint(0, 23),
                                                     minutes=random.randint(0, 59))
            
            status = random.choice(statuts)
            date_resolution = None
            if status == 'Résolu':
                # Resolution date should be after incident date
                hours_to_resolve = random.randint(1, 48)
                date_resolution = incident_date + timedelta(hours=hours_to_resolve)

            incident = Incident(
                wilaya='Blida',
                commune=random.choice(communes_blida),
                localite=random.choice(localites),
                nature_cause=random.choice(natures),
                date_incident=incident_date,
                mesures_prises=random.choice(mesures),
                impact=random.choice(impacts),
                gravite=random.choice(gravites),
                status=status,
                date_resolution=date_resolution,
                user_id=blida_user.id,
                unit_id=blida_unit.id
            )
            db.session.add(incident)
        
        try:
            db.session.commit()
            print("Successfully added 10 example incidents for Unité de Blida")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding incidents: {str(e)}")

if __name__ == '__main__':
    create_example_incidents()
