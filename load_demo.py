"""
Script de chargement des données de démonstration (4 tronçons T1–T4).
Usage : python load_demo.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vizir_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from datetime import date
from troncons.models import Troncon, ParametresTroncon, CoefficientsSimulation, ResultatsSimulation
from troncons.engine import calculer_resultats

TRONCONS_DEMO = [
    {
        'nom': 'T1', 'route': 'Pont Djiri – Péage de Kintélé', 'pk_debut': 'PK0+000', 'pk_fin': 'PK1+250',
        'longueur_m': 1250, 'localisation': 'Brazzaville, Congo',
        'id0_vizir': 3, 'A': 0.70, 'CL': 0.60, 'M': 0.80,
    },
    {
        'nom': 'T2', 'route': 'Pont Djiri – Péage de Kintélé', 'pk_debut': 'PK1+250', 'pk_fin': 'PK2+500',
        'longueur_m': 1250, 'localisation': 'Brazzaville, Congo',
        'id0_vizir': 6, 'A': 1.00, 'CL': 0.80, 'M': 0.60,
    },
    {
        'nom': 'T3', 'route': 'Pont Djiri – Péage de Kintélé', 'pk_debut': 'PK2+500', 'pk_fin': 'PK3+750',
        'longueur_m': 1250, 'localisation': 'Brazzaville, Congo',
        'id0_vizir': 3, 'A': 0.80, 'CL': 1.00, 'M': 0.75,
    },
    {
        'nom': 'T4', 'route': 'Pont Djiri – Péage de Kintélé', 'pk_debut': 'PK3+750', 'pk_fin': 'PK5+000',
        'longueur_m': 1250, 'localisation': 'Brazzaville, Congo',
        'id0_vizir': 7, 'A': 1.20, 'CL': 0.70, 'M': 0.40,
    },
]

for data in TRONCONS_DEMO:
    troncon, created = Troncon.objects.get_or_create(
        nom=data['nom'], route=data['route'],
        defaults={
            'pk_debut': data['pk_debut'], 'pk_fin': data['pk_fin'],
            'longueur_m': data['longueur_m'], 'localisation': data['localisation'],
        }
    )
    if created:
        print(f"  → Tronçon {troncon.nom} créé")

    coeffs, _ = CoefficientsSimulation.objects.get_or_create(troncon=troncon)

    params = ParametresTroncon.objects.create(
        troncon=troncon,
        date_inspection=date(2024, 6, 1),
        id0_vizir=data['id0_vizir'],
        mode_A='direct', A=data['A'],
        mode_CL='direct', CL=data['CL'],
        mode_M='direct', M=data['M'],
    )

    res = calculer_resultats(
        ID0=data['id0_vizir'], A=data['A'], CL=data['CL'], M=data['M'],
        alpha=0.40, beta=0.35, gamma=0.25,
        horizons=[1, 5, 10, 15],
    )

    ResultatsSimulation.objects.create(
        troncon=troncon, parametres=params,
        R=res['R'],
        contrib_trafic=res['contrib_trafic'],
        contrib_climat=res['contrib_climat'],
        contrib_materiau=res['contrib_materiau'],
        contrib_trafic_pct=res['contrib_trafic_pct'],
        contrib_climat_pct=res['contrib_climat_pct'],
        contrib_materiau_pct=res['contrib_materiau_pct'],
        facteur_dominant=res['facteur_dominant'],
        niveau_risque=res['niveau_risque'],
        t_critique_ans=res['t_critique'],
        projections_json={str(k): v for k, v in res['projections'].items()},
        recommandations='\n'.join(res['recommandations']),
        alpha_utilise=0.40, beta_utilise=0.35, gamma_utilise=0.25,
    )
    print(f"  ✅ {troncon.nom} — R={res['R']} pts/an — Risque: {res['niveau_risque']}")

print("\nDonnées de démonstration chargées avec succès !")
