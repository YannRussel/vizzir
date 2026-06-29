from django.contrib import admin
from .models import Troncon, ParametresTroncon, CoefficientsSimulation, ResultatsSimulation


@admin.register(Troncon)
class TronconAdmin(admin.ModelAdmin):
    list_display = ['nom', 'route', 'localisation', 'date_creation']
    search_fields = ['nom', 'route', 'localisation']


@admin.register(ParametresTroncon)
class ParametresTronconAdmin(admin.ModelAdmin):
    list_display = ['troncon', 'date_inspection', 'id0_vizir', 'mode_A', 'mode_CL', 'mode_M']
    list_filter = ['mode_A', 'mode_CL', 'mode_M']


@admin.register(CoefficientsSimulation)
class CoefficientsAdmin(admin.ModelAdmin):
    list_display = ['troncon', 'alpha', 'beta', 'gamma', 'seuil_critique_ans', 'seuil_eleve_ans']


@admin.register(ResultatsSimulation)
class ResultatsAdmin(admin.ModelAdmin):
    list_display = ['troncon', 'date_calcul', 'R', 'facteur_dominant', 'niveau_risque', 't_critique_ans']
    list_filter = ['niveau_risque', 'facteur_dominant']
    readonly_fields = ['date_calcul']
