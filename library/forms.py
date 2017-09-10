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
    num_options = [('-1', 'Any'), ('0-10', 'Less than or equal to 10'), ('11-100', 'Between 11 and 100'), ('101-99999', 'More than 100')]
    ratio_options = [('-1', 'Any'), ('0-50', 'Lesson than or equal to 0.5'), ('51-100', '0.5-1'), ('101-99999', 'More than 1')]

    num_tables = forms.ChoiceField(choices=num_options, required = False, label = '# of Tables', widget=forms.Select(attrs={'class':'form-control'}))
    num_indexes = forms.ChoiceField(choices=num_options, required = False, label = '# of Indexes', widget=forms.Select(attrs={'class':'form-control'}))
    num_secondary_indexes = forms.ChoiceField(choices=num_options, required = False, label = '# of Secondary Indexes', widget=forms.Select(attrs={'class':'form-control'}))
    num_constraints = forms.ChoiceField(choices=num_options, required = False, label = '# of Constraints', widget=forms.Select(attrs={'class':'form-control'}))
    num_foreignkeys = forms.ChoiceField(choices=num_options, required = False, label = '# of Foreign Keys', widget=forms.Select(attrs={'class':'form-control'}))
    num_transactions = forms.ChoiceField(choices=num_options, required = False, label = '# of Transactions', widget=forms.Select(attrs={'class':'form-control'}))
    transaction_ratio = forms.ChoiceField(choices=ratio_options, required = False, label = 'Ratio of Txn/Action', widget=forms.Select(attrs={'class':'form-control'}))

    coverage_options = [('-1', 'Any'), ('0-20', 'Less than 20'), ('21-40', '21-40'), ('41-60', '41-60'), ('61-80', '61-80'), ('81-100', '81-100')]
    table_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Table Coverage', widget=forms.Select(attrs={'class':'form-control'}))
    column_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Column Coverage', widget=forms.Select(attrs={'class':'form-control'}))
    # index_coverage = forms.ChoiceField(choices=coverage_options, required = False, label = 'Index Coverage', widget=forms.Select(attrs={'class':'form-control'}))

