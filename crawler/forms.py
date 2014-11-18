from django import forms
from models import *

class ResultForm(forms.Form):
    options = Result.objects.all().values_list('name', 'name')
    results = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=options)

class TypeForm(forms.Form):
    options = Type.objects.all().values_list('name', 'name')
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=options)
