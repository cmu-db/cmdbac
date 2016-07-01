from django import forms
from models import *
from django.template.loader import render_to_string
from django.forms.fields import EMPTY_VALUES
from django.utils.translation import ugettext as _


class ResultForm(forms.Form):
    results = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=reversed(ATTEMPT_STATUS),
                        required=False,
                        label="Latest Attempt Status")

class ProjectTypeForm(forms.Form):
    options = ProjectType.objects.all().values_list('name', 'name')
    types = forms.MultipleChoiceField(
                        widget=forms.CheckboxSelectMultiple,
                        choices=options,
                        required=False,
                        label="Project Type")

class StatisticsForm(forms.Form):
    num_options = [('-1', 'Any'), ('0-10', 'Less than 10'), ('11-100', 'Between 11 and 100'), ('101-99999', 'More than 100')]
    num_tables = forms.ChoiceField(choices=num_options, required = False, label = '# of Tables', widget=forms.Select(attrs={'class':'form-control'}))
    num_indexes = forms.ChoiceField(choices=num_options, required = False, label = '# of Indexes', widget=forms.Select(attrs={'class':'form-control'}))
    num_secondary_indexes = forms.ChoiceField(choices=num_options, required = False, label = '# of Secondary Indexes', widget=forms.Select(attrs={'class':'form-control'}))
    num_constraints = forms.ChoiceField(choices=num_options, required = False, label = '# of Constraints', widget=forms.Select(attrs={'class':'form-control'}))
    num_foreignkeys = forms.ChoiceField(choices=num_options, required = False, label = '# of Foreign Keys', widget=forms.Select(attrs={'class':'form-control'}))
    num_transactions = forms.ChoiceField(choices=num_options, required = False, label = '# of Transactions', widget=forms.Select(attrs={'class':'form-control'}))
    
    coverage_options = [('-1', 'Any'), ('0-20', 'Less than 20'), ('20-40', '20-40'), ('40-60', '40-60'), ('60-80', '60-80'), ('80-100', '80-100')]
    table_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Table Coverage', widget=forms.Select(attrs={'class':'form-control'}))
    column_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Column Coverage', widget=forms.Select(attrs={'class':'form-control'}))
    # index_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Index Coverage', widget=forms.Select(attrs={'class':'form-control'}))
