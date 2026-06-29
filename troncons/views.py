from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages

from .models import Troncon, ParametresTroncon, CoefficientsSimulation, ResultatsSimulation
from .forms import TronconForm, ParametresForm, CoefficientsForm
from .engine import calculer_resultats, run_tests
from .exports import export_pdf, export_excel


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
def dashboard(request):
    troncons = Troncon.objects.prefetch_related('resultats').all()
    stats = {
        'total':    troncons.count(),
        'critique': sum(1 for t in troncons if t.get_last_resultats() and t.get_last_resultats().niveau_risque == 'Critique'),
        'eleve':    sum(1 for t in troncons if t.get_last_resultats() and t.get_last_resultats().niveau_risque == 'Élevé'),
        'modere':   sum(1 for t in troncons if t.get_last_resultats() and t.get_last_resultats().niveau_risque in ('Modéré', 'Modéré (stable)')),
    }
    return render(request, 'troncons/dashboard.html', {'troncons': troncons, 'stats': stats})


# ─────────────────────────────────────────
# TRONÇON CRUD
# ─────────────────────────────────────────
def troncon_create(request):
    if request.method == 'POST':
        form = TronconForm(request.POST)
        if form.is_valid():
            troncon = form.save()
            CoefficientsSimulation.objects.get_or_create(troncon=troncon)
            messages.success(request, f"Tronçon « {troncon.nom} » créé avec succès.")
            return redirect('troncon_detail', pk=troncon.pk)
    else:
        form = TronconForm()
    return render(request, 'troncons/troncon_form.html', {'form': form, 'titre': 'Nouveau tronçon'})


def troncon_detail(request, pk):
    troncon = get_object_or_404(Troncon, pk=pk)
    resultats = troncon.resultats.order_by('-date_calcul')
    last_resultat = resultats.first()
    coeffs, _ = CoefficientsSimulation.objects.get_or_create(troncon=troncon)
    return render(request, 'troncons/troncon_detail.html', {
        'troncon': troncon,
        'resultats': resultats,
        'last_resultat': last_resultat,
        'coeffs': coeffs,
    })


def troncon_edit(request, pk):
    troncon = get_object_or_404(Troncon, pk=pk)
    if request.method == 'POST':
        form = TronconForm(request.POST, instance=troncon)
        if form.is_valid():
            form.save()
            messages.success(request, "Tronçon mis à jour.")
            return redirect('troncon_detail', pk=pk)
    else:
        form = TronconForm(instance=troncon)
    return render(request, 'troncons/troncon_form.html', {'form': form, 'titre': f'Modifier {troncon.nom}', 'troncon': troncon})


def troncon_delete(request, pk):
    troncon = get_object_or_404(Troncon, pk=pk)
    if request.method == 'POST':
        nom = troncon.nom
        troncon.delete()
        messages.success(request, f"Tronçon « {nom} » supprimé.")
        return redirect('dashboard')
    return render(request, 'troncons/troncon_confirm_delete.html', {'troncon': troncon})


# ─────────────────────────────────────────
# SAISIE DONNÉES + CALCUL
# ─────────────────────────────────────────
def saisie_parametres(request, pk):
    troncon = get_object_or_404(Troncon, pk=pk)
    coeffs, _ = CoefficientsSimulation.objects.get_or_create(troncon=troncon)

    if request.method == 'POST':
        form_p = ParametresForm(request.POST)
        form_c = CoefficientsForm(request.POST, instance=coeffs)
        if form_p.is_valid() and form_c.is_valid():
            coeffs = form_c.save()
            parametres = form_p.save(commit=False)
            parametres.troncon = troncon
            parametres.save()

            A  = parametres.get_A()
            CL = parametres.get_CL()
            M  = parametres.get_M()
            horizons = form_p.cleaned_data.get('horizons', [1, 5, 10, 15])

            res = calculer_resultats(
                ID0=parametres.id0_vizir,
                A=A, CL=CL, M=M,
                alpha=coeffs.alpha, beta=coeffs.beta, gamma=coeffs.gamma,
                seuil_critique=coeffs.seuil_critique_ans,
                seuil_eleve=coeffs.seuil_eleve_ans,
                horizons=horizons,
            )

            ResultatsSimulation.objects.create(
                troncon=troncon,
                parametres=parametres,
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
                alpha_utilise=coeffs.alpha,
                beta_utilise=coeffs.beta,
                gamma_utilise=coeffs.gamma,
            )

            messages.success(request, "Calcul effectué et résultats enregistrés.")
            return redirect('troncon_detail', pk=pk)
    else:
        form_p = ParametresForm()
        form_c = CoefficientsForm(instance=coeffs)

    return render(request, 'troncons/saisie_parametres.html', {
        'troncon': troncon,
        'form_p': form_p,
        'form_c': form_c,
    })


# ─────────────────────────────────────────
# VUE COMPARATIVE
# ─────────────────────────────────────────
def comparatif(request):
    troncons = Troncon.objects.all()
    donnees = []
    for t in troncons:
        r = t.get_last_resultats()
        if r:
            donnees.append({'troncon': t, 'resultat': r})
    return render(request, 'troncons/comparatif.html', {'donnees': donnees})


# ─────────────────────────────────────────
# EXPORTS
# ─────────────────────────────────────────
def export_pdf_view(request, pk):
    troncon = get_object_or_404(Troncon, pk=pk)
    last_resultat = troncon.get_last_resultats()
    if not last_resultat:
        messages.error(request, "Aucun résultat à exporter.")
        return redirect('troncon_detail', pk=pk)
    buffer = export_pdf(troncon, last_resultat)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vizir_{troncon.nom}.pdf"'
    return response


def export_excel_view(request):
    troncons = Troncon.objects.all()
    donnees = [{'troncon': t, 'resultat': t.get_last_resultats()} for t in troncons if t.get_last_resultats()]
    buffer = export_excel(donnees)
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="vizir_comparatif.xlsx"'
    return response


# ─────────────────────────────────────────
# TESTS DE VALIDATION
# ─────────────────────────────────────────
def tests_validation(request):
    resultats = run_tests()
    tous_ok = all(r['passed'] for r in resultats)
    return render(request, 'troncons/tests.html', {'resultats': resultats, 'tous_ok': tous_ok})