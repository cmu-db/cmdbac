from django import forms
from models import *

class ResultForm(forms.Form):
    results = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=ATTEMPT_STATUS, required=False)

class TypeForm(forms.Form):
    options = Type.objects.all().values_list('name', 'name')
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=options, required=False)
