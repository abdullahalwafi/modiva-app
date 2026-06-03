from django import forms


class AnemiaPredictionForm(forms.Form):
    HGB = forms.DecimalField(label='Hemoglobin (HGB)', max_digits=5, decimal_places=2, min_value=0)
    HCT = forms.DecimalField(label='Hematokrit (HCT)', max_digits=5, decimal_places=2, min_value=0)
    RBC = forms.DecimalField(label='Sel Darah Merah (RBC)', max_digits=5, decimal_places=2, min_value=0)
    MCH = forms.DecimalField(label='MCH', max_digits=5, decimal_places=2, min_value=0)
    MCHC = forms.DecimalField(label='MCHC', max_digits=5, decimal_places=2, min_value=0)

    def as_feature_dict(self):
        return {
            key: float(self.cleaned_data[key])
            for key in ['HGB', 'HCT', 'RBC', 'MCH', 'MCHC']
        }
