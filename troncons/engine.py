"""
Moteur de calcul VIZIR — modèle de dégradation des chaussées flexibles.
Séparé de Django pour être testable indépendamment et remplaçable par un module IA futur.
"""


RECOMMANDATIONS = {
    'Trafic (αA)': [
        "Limitation du trafic lourd",
        "Contrôle des charges à l'essieu",
        "Réglementation des convois exceptionnels",
        "Réorientation des flux vers des itinéraires adaptés",
        "Renforcement structurel de la chaussée",
    ],
    'Trafic + Climat': [
        "Limitation du trafic lourd",
        "Contrôle des charges à l'essieu",
        "Amélioration du drainage",
        "Curage des caniveaux",
        "Renforcement structurel de la chaussée",
        "Matériaux adaptés aux conditions climatiques locales",
    ],
    'Climat (βCL)': [
        "Amélioration du drainage",
        "Curage des caniveaux",
        "Réhabilitation des ouvrages hydrauliques",
        "Correction des pentes transversales",
        "Protection des accotements",
        "Matériaux adaptés aux conditions climatiques locales",
    ],
    'Matériau (γM)': [
        "Renforcement de la couche de roulement",
        "Augmentation de l'épaisseur structurelle",
        "Amélioration des matériaux utilisés",
        "Traitement des couches de fondation",
        "Reconstruction partielle des sections les plus dégradées",
    ],
    'Stable': [
        "Entretien préventif courant",
        "Surveillance périodique de l'état de surface",
        "Maintien du drainage existant",
    ],
}


def calculer_A_detaille(N_PL, CAM, Nref):
    """Calcule A depuis les données détaillées de trafic."""
    Ne = N_PL * CAM
    return Ne / Nref


def calculer_CL_detaille(P, T, H, w1=0.4, w2=0.35, w3=0.25):
    """Calcule CL depuis les données climatiques détaillées."""
    return w1 * P + w2 * T + w3 * H


def calculer_M_detaille(CBR, eref):
    """Calcule M depuis le CBR et l'épaisseur de référence."""
    e = 482.4 / (CBR + 5)
    return e / eref


def get_facteur_dominant(contrib_trafic, contrib_climat, seuil_proximite=0.10):
    """
    Identifie le facteur dominant entre trafic et climat.
    Si les deux sont proches (écart < seuil), retourne 'Trafic + Climat'.
    """
    if contrib_trafic <= 0 and contrib_climat <= 0:
        return 'Matériau (γM)'

    max_contrib = max(contrib_trafic, contrib_climat)
    if max_contrib == 0:
        return 'Matériau (γM)'

    ecart_relatif = abs(contrib_trafic - contrib_climat) / max_contrib
    if ecart_relatif < seuil_proximite:
        return 'Trafic + Climat'
    elif contrib_trafic >= contrib_climat:
        return 'Trafic (αA)'
    else:
        return 'Climat (βCL)'


def calculer_resultats(
    ID0,
    A,
    CL,
    M,
    alpha=0.40,
    beta=0.35,
    gamma=0.25,
    seuil_critique=2.0,
    seuil_eleve=10.0,
    horizons=None,
    seuil_proximite=0.10,
):
    """
    Moteur de calcul principal VIZIR.

    Paramètres :
        ID0 : indice VIZIR initial (0–7)
        A   : agressivité du trafic (normalisée)
        CL  : coefficient climatique (normalisé)
        M   : paramètre matériau (normalisé)
        alpha, beta, gamma : coefficients de pondération
        seuil_critique : seuil en années pour le risque Critique
        seuil_eleve    : seuil en années pour le risque Élevé
        horizons       : liste d'horizons de projection en années

    Retourne un dictionnaire complet avec tous les résultats.
    """
    if horizons is None:
        horizons = [1, 5, 10, 15]

    # --- Étape 1 : Rythme de dégradation ---
    contrib_trafic = alpha * A
    contrib_climat = beta * CL
    contrib_materiau = -gamma * M
    R = contrib_trafic + contrib_climat + contrib_materiau

    # --- Étape 2 : Projections temporelles (plafonnées à 7) ---
    projections = {}
    for t in horizons:
        projections[t] = min(7.0, ID0 + R * t)

    # --- Étape 3 : Facteur dominant ---
    facteur_dominant = get_facteur_dominant(contrib_trafic, contrib_climat, seuil_proximite)

    # --- Étape 4 : Contributions relatives (%) ---
    if R != 0:
        contrib_trafic_pct = (contrib_trafic / R) * 100
        contrib_climat_pct = (contrib_climat / R) * 100
        contrib_materiau_pct = (contrib_materiau / R) * 100
    else:
        contrib_trafic_pct = 0.0
        contrib_climat_pct = 0.0
        contrib_materiau_pct = 0.0

    # --- Étape 5 : Niveau de risque ---
    if ID0 >= 7:
        t_critique = 0.0
    elif R <= 0:
        # Chaussée stable ou en amélioration — pas de dégradation prévisible
        t_critique = None
    else:
        t_critique = (7.0 - ID0) / R

    if t_critique is None:
        niveau_risque = "Modéré (stable)"
    elif t_critique <= seuil_critique:
        niveau_risque = "Critique"
    elif t_critique <= seuil_eleve:
        niveau_risque = "Élevé"
    else:
        niveau_risque = "Modéré"

    # --- Étape 6 : Recommandations ---
    cle_reco = facteur_dominant if R > 0 else 'Stable'
    recommandations = RECOMMANDATIONS.get(cle_reco, RECOMMANDATIONS['Stable'])

    return {
        "ID0": ID0,
        "A": A,
        "CL": CL,
        "M": M,
        "R": round(R, 4),
        "contrib_trafic": round(contrib_trafic, 4),
        "contrib_climat": round(contrib_climat, 4),
        "contrib_materiau": round(contrib_materiau, 4),
        "contrib_trafic_pct": round(contrib_trafic_pct, 2),
        "contrib_climat_pct": round(contrib_climat_pct, 2),
        "contrib_materiau_pct": round(contrib_materiau_pct, 2),
        "projections": projections,
        "facteur_dominant": facteur_dominant,
        "t_critique": round(t_critique, 2) if t_critique is not None else None,
        "niveau_risque": niveau_risque,
        "recommandations": recommandations,
    }


# --- Tests de non-régression (section 10 du cahier des charges) ---
CAS_TEST = [
    # (ID0, A, CL, M, alpha, beta, gamma, R_attendu, ID5_attendu, ID10_attendu, risque_attendu)
    (3, 0.70, 0.60, 0.80, 0.40, 0.35, 0.25, 0.29, 4.45, 5.90, "Modéré"),
    (6, 1.00, 0.80, 0.60, 0.40, 0.35, 0.25, 0.53, 7.0,  7.0,  "Critique"),
    (3, 0.80, 1.00, 0.75, 0.40, 0.35, 0.25, 0.48, 5.40, 7.0,  "Élevé"),
    (7, 1.20, 0.70, 0.40, 0.40, 0.35, 0.25, 0.63, 7.0,  7.0,  "Critique"),
]


def run_tests():
    """Valide le moteur contre les 4 cas de test du cahier des charges."""
    resultats_tests = []
    for i, (ID0, A, CL, M, alpha, beta, gamma, R_att, ID5_att, ID10_att, risque_att) in enumerate(CAS_TEST, 1):
        res = calculer_resultats(ID0, A, CL, M, alpha, beta, gamma)
        ok_R = abs(res['R'] - R_att) < 0.02
        ok_ID5 = abs(res['projections'][5] - ID5_att) < 0.02
        ok_ID10 = abs(res['projections'][10] - ID10_att) < 0.02
        ok_risque = res['niveau_risque'] == risque_att
        passed = ok_R and ok_ID5 and ok_ID10 and ok_risque
        resultats_tests.append({
            'cas': i,
            'passed': passed,
            'ID0': ID0,
            'R_attendu': R_att, 'R_calcule': res['R'],
            'ID5_attendu': ID5_att, 'ID5_calcule': res['projections'][5],
            'ID10_attendu': ID10_att, 'ID10_calcule': res['projections'][10],
            'risque_attendu': risque_att, 'risque_calcule': res['niveau_risque'],
        })
    return resultats_tests
