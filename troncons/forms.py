from django import forms
from .models import Troncon, ParametresTroncon, CoefficientsSimulation


class CommaDecimalField(forms.FloatField):
    """Champ numérique qui accepte la virgule ET le point comme séparateur décimal."""
    def to_python(self, value):
        if value:
            value = str(value).replace(',', '.')
        return super().to_python(value)


class TronconForm(forms.ModelForm):
    class Meta:
        model = Troncon
        fields = ['nom', 'route', 'pk_debut', 'pk_fin', 'longueur_m', 'localisation']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. T1'}),
            'route': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. RN1 Brazzaville–Kintélé'}),
            'pk_debut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. PK0+000'}),
            'pk_fin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. PK1+250'}),
            'longueur_m': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'localisation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. Brazzaville, Congo'}),
        }


class ParametresForm(forms.ModelForm):
    horizons = forms.CharField(
        initial='1,5,10,15',
        label='Horizons de projection (années, séparés par virgules)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1,5,10,15'}),
        help_text='Saisir les horizons en années séparés par des virgules'
    )

    # Remplacement des FloatField Django par notre champ virgule-compatible
    A   = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex. 0.70'}))
    CL  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex. 0.60'}))
    M   = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex. 0.80'}))
    N_PL = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}))
    CAM  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}))
    Nref = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}))
    P  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    T  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    H  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    w1 = CommaDecimalField(required=False, initial=0.4, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    w2 = CommaDecimalField(required=False, initial=0.35, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    w3 = CommaDecimalField(required=False, initial=0.25, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    CBR  = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    eref = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    dc_deflexion = CommaDecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))

    class Meta:
        model = ParametresTroncon
        fields = [
            'date_inspection', 'id0_vizir',
            'mode_A', 'A', 'N_PL', 'CAM', 'Nref',
            'mode_CL', 'CL', 'P', 'T', 'H', 'w1', 'w2', 'w3',
            'mode_M', 'M', 'CBR', 'eref',
            'dc_deflexion', 'degradations_observees',
        ]
        widgets = {
            'date_inspection': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'id0_vizir': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 7}),
            'mode_A':  forms.Select(attrs={'class': 'form-select'}),
            'mode_CL': forms.Select(attrs={'class': 'form-select'}),
            'mode_M':  forms.Select(attrs={'class': 'form-select'}),
            'degradations_observees': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_horizons(self):
        raw = self.cleaned_data.get('horizons', '1,5,10,15')
        try:
            horizons = [float(h.strip().replace(',', '.')) for h in raw.replace(';', ',').split(',') if h.strip()]
            if not horizons:
                raise forms.ValidationError("Saisir au moins un horizon.")
            return horizons
        except ValueError:
            raise forms.ValidationError("Format invalide. Exemple : 1,5,10,15")

    def clean(self):
        cleaned = super().clean()
        mode_A  = cleaned.get('mode_A')
        mode_CL = cleaned.get('mode_CL')
        mode_M  = cleaned.get('mode_M')

        if mode_A == 'direct' and cleaned.get('A') is None:
            self.add_error('A', 'Valeur A requise en mode direct.')
        if mode_A == 'detaille':
            for f in ['N_PL', 'CAM', 'Nref']:
                if cleaned.get(f) is None:
                    self.add_error(f, 'Champ requis en mode détaillé.')

        if mode_CL == 'direct' and cleaned.get('CL') is None:
            self.add_error('CL', 'Valeur CL requise en mode direct.')
        if mode_CL == 'detaille':
            for f in ['P', 'T', 'H']:
                if cleaned.get(f) is None:
                    self.add_error(f, 'Champ requis en mode détaillé.')

        if mode_M == 'direct' and cleaned.get('M') is None:
            self.add_error('M', 'Valeur M requise en mode direct.')
        if mode_M == 'detaille':
            for f in ['CBR', 'eref']:
                if cleaned.get(f) is None:
                    self.add_error(f, 'Champ requis en mode détaillé.')

        return cleaned


class CoefficientsForm(forms.ModelForm):
    alpha  = CommaDecimalField(initial=0.40, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    beta   = CommaDecimalField(initial=0.35, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    gamma  = CommaDecimalField(initial=0.25, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    seuil_critique_ans = CommaDecimalField(initial=2.0,  widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}))
    seuil_eleve_ans    = CommaDecimalField(initial=10.0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}))

    class Meta:
        model = CoefficientsSimulation
        fields = ['alpha', 'beta', 'gamma', 'seuil_critique_ans', 'seuil_eleve_ans']