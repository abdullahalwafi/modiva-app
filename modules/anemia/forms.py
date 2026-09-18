from django import forms


class AnemiaPredictionForm(forms.Form):
    HB = forms.DecimalField(label='Kadar HB (g/dL)', max_digits=5, decimal_places=2, min_value=0)

    def as_feature_dict(self):
        return {
            key: float(self.cleaned_data[key])
            for key in ['HB']
        }
