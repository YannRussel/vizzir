# VIZIR — Logiciel de Modélisation et Suivi de la Dégradation des Chaussées

Application Django conforme au cahier des charges du mémoire de Christian Dandy Noble MALELA (ISAUBTP-CMI).

---

## Installation rapide

```bash
# 1. Se placer dans le dossier du projet
cd vizir_project

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer la base de données
python manage.py migrate

# 4. (Optionnel) Charger les 4 tronçons de démonstration T1–T4
python load_demo.py

# 5. (Optionnel) Créer un compte administrateur
python manage.py createsuperuser

# 6. Lancer le serveur
python manage.py runserver
```

L'application est accessible sur : **http://127.0.0.1:8000/**

---

## Fonctionnalités

### Moteur de calcul (engine.py)
- `R = α·A + β·CL − γ·M` (coefficients paramétrables, défauts : α=0,40 / β=0,35 / γ=0,25)
- `ID(t) = min(7, ID₀ + R·t)` avec plafonnement automatique
- Identification du facteur dominant (Trafic / Climat / Trafic+Climat / Matériau)
- Calcul T_critique = (7 − ID₀) / R avec gestion des cas R≤0 (stable)
- 4 tests de non-régression validés (section 10 du cahier des charges)

### Double mode de saisie pour A, CL, M
- **Mode direct** : saisie de la valeur normalisée
- **Mode détaillé** : calcul automatique depuis N_PL/CAM/Nref, P/T/H/w1/w2/w3, CBR/eref

### Interface
- **Dashboard** : vue globale avec stats Critique / Élevé / Modéré
- **Fiche tronçon** : résultats, graphiques, historique des inspections
- **Vue comparative** : tableau et 4 graphiques pour tous les tronçons
- **Saisie** : formulaire adaptatif (mode direct / détaillé)
- **Tests** : page de validation du moteur

### Exports
- **PDF** (ReportLab) : rapport complet par tronçon
- **Excel** (openpyxl) : tableau comparatif formaté

### Graphiques (Matplotlib)
1. Paramètres A, CL, M par tronçon (barres groupées)
2. Contributions au rythme R (barres simples)
3. Projection ID(t) multi-tronçons avec seuil critique
4. Contributions relatives (%) par tronçon

---

## Structure du projet

```
vizir_project/
├── manage.py
├── load_demo.py          # Charge les 4 tronçons de démo
├── requirements.txt
├── db.sqlite3            # Base de données (créée au 1er migrate)
├── vizir_project/
│   ├── settings.py
│   └── urls.py
└── troncons/
    ├── models.py         # Troncon, ParametresTroncon, CoefficientsSimulation, ResultatsSimulation
    ├── engine.py         # 🔑 Moteur de calcul VIZIR (testable indépendamment)
    ├── forms.py          # Formulaires avec double mode de saisie
    ├── views.py          # Vues + génération graphiques
    ├── exports.py        # PDF et Excel
    ├── urls.py
    └── templates/
```

---

## Tests de non-régression

```bash
python -c "
from troncons.engine import run_tests
for r in run_tests():
    print(f\"T{r['cas']}: {'✅ PASS' if r['passed'] else '❌ FAIL'}\")
"
```

Résultats attendus : T1 ✅ T2 ✅ T3 ✅ T4 ✅

---

## Architecture modulaire (préparation aux évolutions futures)

Le moteur de calcul (`engine.py`) est **totalement séparé** de Django.  
Il peut être remplacé par un module RNA/IA sans modifier la couche données ni l'interface.  
API REST possible via Django REST Framework ou les vues JSON existantes.
