from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('troncon/nouveau/', views.troncon_create, name='troncon_create'),
    path('troncon/<int:pk>/', views.troncon_detail, name='troncon_detail'),
    path('troncon/<int:pk>/modifier/', views.troncon_edit, name='troncon_edit'),
    path('troncon/<int:pk>/supprimer/', views.troncon_delete, name='troncon_delete'),
    path('troncon/<int:pk>/saisie/', views.saisie_parametres, name='saisie_parametres'),
    path('troncon/<int:pk>/export-pdf/', views.export_pdf_view, name='export_pdf'),
    path('comparatif/', views.comparatif, name='comparatif'),
    path('comparatif/export-excel/', views.export_excel_view, name='export_excel'),
    path('tests/', views.tests_validation, name='tests_validation'),
]
