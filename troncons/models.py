from django.db import models
from django.utils import timezone


class Troncon(models.Model):
    """Unité d'analyse : une section homogène de chaussée flexible."""
    nom = models.CharField(max_length=100, verbose_name="Identifiant du tronçon")
    route = models.CharField(max_length=200, verbose_name="Nom de la route", blank=True)
    pk_debut = models.CharField(max_length=50, verbose_name="PK début", blank=True)
    pk_fin = models.CharField(max_length=50, verbose_name="PK fin", blank=True)
    longueur_m = models.FloatField(verbose_name="Longueur (m)", null=True, blank=True)
    localisation = models.CharField(max_length=300, verbose_name="Localisation / pays", blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Tronçon"
        verbose_name_plural = "Tronçons"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} — {self.route or 'Route non précisée'}"

    def get_last_parametres(self):
        return self.parametres.order_by('-date_inspection').first()

    def get_last_resultats(self):
        return self.resultats.order_by('-date_calcul').first()


class ParametresTroncon(models.Model):
    """Données d'entrée d'une inspection VIZIR pour un tronçon."""
    troncon = models.ForeignKey(Troncon, on_delete=models.CASCADE, related_name='parametres')
    date_inspection = models.DateField(verbose_name="Date de l'auscultation")

    # Indice VIZIR
    id0_vizir = models.IntegerField(
        verbose_name="Indice VIZIR observé (Is = ID₀)",
        help_text="Entier de 0 à 7"
    )

    # --- MODE DE SAISIE A ---
    MODE_CHOICES = [('direct', 'Valeur directe'), ('detaille', 'Calcul détaillé')]
    mode_A = models.CharField(max_length=10, choices=MODE_CHOICES, default='direct', verbose_name="Mode saisie A")
    A = models.FloatField(verbose_name="Agressivité du trafic (A)", null=True, blank=True)
    # Mode détaillé A
    N_PL = models.FloatField(verbose_name="Nombre cumulé de poids lourds (N_PL)", null=True, blank=True)
    CAM = models.FloatField(verbose_name="Coefficient d'agressivité moyen (CAM)", null=True, blank=True)
    Nref = models.FloatField(verbose_name="Nombre d'essieux de référence (Nref)", null=True, blank=True)

    # --- MODE DE SAISIE CL ---
    mode_CL = models.CharField(max_length=10, choices=MODE_CHOICES, default='direct', verbose_name="Mode saisie CL")
    CL = models.FloatField(verbose_name="Coefficient climatique (CL)", null=True, blank=True)
    # Mode détaillé CL
    P = models.FloatField(verbose_name="Pluviométrie normalisée (P)", null=True, blank=True)
    T = models.FloatField(verbose_name="Température normalisée (T)", null=True, blank=True)
    H = models.FloatField(verbose_name="Humidité normalisée (H)", null=True, blank=True)
    w1 = models.FloatField(verbose_name="Poids w1 (pluviométrie)", null=True, blank=True, default=0.4)
    w2 = models.FloatField(verbose_name="Poids w2 (température)", null=True, blank=True, default=0.35)
    w3 = models.FloatField(verbose_name="Poids w3 (humidité)", null=True, blank=True, default=0.25)

    # --- MODE DE SAISIE M ---
    mode_M = models.CharField(max_length=10, choices=MODE_CHOICES, default='direct', verbose_name="Mode saisie M")
    M = models.FloatField(verbose_name="Paramètre matériau (M)", null=True, blank=True)
    # Mode détaillé M
    CBR = models.FloatField(verbose_name="Indice CBR (%)", null=True, blank=True)
    eref = models.FloatField(verbose_name="Épaisseur de référence (cm)", null=True, blank=True)

    # Données descriptives optionnelles
    dc_deflexion = models.FloatField(
        verbose_name="Déflexion caractéristique dc (1/100 mm)",
        null=True, blank=True
    )
    degradations_observees = models.TextField(
        verbose_name="Types de dégradations observées",
        blank=True,
        help_text="Ex. faïençage, nid de poule, orniérage..."
    )

    class Meta:
        verbose_name = "Paramètres d'inspection"
        verbose_name_plural = "Paramètres d'inspection"
        ordering = ['-date_inspection']

    def __str__(self):
        return f"{self.troncon.nom} — inspection {self.date_inspection}"

    def get_A(self):
        if self.mode_A == 'direct':
            return self.A
        if self.N_PL and self.CAM and self.Nref:
            Ne = self.N_PL * self.CAM
            return Ne / self.Nref
        return None

    def get_CL(self):
        if self.mode_CL == 'direct':
            return self.CL
        if self.P is not None and self.T is not None and self.H is not None:
            return self.w1 * self.P + self.w2 * self.T + self.w3 * self.H
        return None

    def get_M(self):
        if self.mode_M == 'direct':
            return self.M
        if self.CBR is not None and self.eref:
            e = 482.4 / (self.CBR + 5)
            return e / self.eref
        return None


class CoefficientsSimulation(models.Model):
    """Coefficients α, β, γ et seuils de risque — paramétrables par tronçon."""
    troncon = models.OneToOneField(Troncon, on_delete=models.CASCADE, related_name='coefficients')
    alpha = models.FloatField(default=0.40, verbose_name="α (trafic)")
    beta = models.FloatField(default=0.35, verbose_name="β (climat)")
    gamma = models.FloatField(default=0.25, verbose_name="γ (matériau)")
    seuil_critique_ans = models.FloatField(default=2.0, verbose_name="Seuil Critique (années)")
    seuil_eleve_ans = models.FloatField(default=10.0, verbose_name="Seuil Élevé (années)")

    class Meta:
        verbose_name = "Coefficients de simulation"

    def __str__(self):
        return f"Coefficients de {self.troncon.nom} (α={self.alpha}, β={self.beta}, γ={self.gamma})"


class ResultatsSimulation(models.Model):
    """Résultats calculés pour un tronçon à partir d'une inspection."""
    troncon = models.ForeignKey(Troncon, on_delete=models.CASCADE, related_name='resultats')
    parametres = models.ForeignKey(
        ParametresTroncon, on_delete=models.CASCADE, related_name='resultats', null=True
    )
    date_calcul = models.DateTimeField(default=timezone.now)

    # Rythme de dégradation
    R = models.FloatField(verbose_name="Rythme de dégradation R (pts/an)")

    # Contributions absolues
    contrib_trafic = models.FloatField()
    contrib_climat = models.FloatField()
    contrib_materiau = models.FloatField()

    # Contributions relatives (%)
    contrib_trafic_pct = models.FloatField(default=0)
    contrib_climat_pct = models.FloatField(default=0)
    contrib_materiau_pct = models.FloatField(default=0)

    # Facteur dominant et risque
    facteur_dominant = models.CharField(max_length=50)
    niveau_risque = models.CharField(max_length=20)
    t_critique_ans = models.FloatField(verbose_name="Temps avant ID=7 (années)", null=True)

    # Projections temporelles (JSON)
    projections_json = models.JSONField(default=dict, verbose_name="Projections ID(t)")

    # Recommandations
    recommandations = models.TextField()

    # Coefficients utilisés (snapshot)
    alpha_utilise = models.FloatField(default=0.40)
    beta_utilise = models.FloatField(default=0.35)
    gamma_utilise = models.FloatField(default=0.25)

    class Meta:
        verbose_name = "Résultats de simulation"
        verbose_name_plural = "Résultats de simulation"
        ordering = ['-date_calcul']

    def __str__(self):
        return f"{self.troncon.nom} — R={self.R:.2f}, Risque: {self.niveau_risque}"

    def get_projections_display(self):
        """Retourne les projections triées par horizon."""
        return sorted(self.projections_json.items(), key=lambda x: float(x[0]))
