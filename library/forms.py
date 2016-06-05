from django import forms
from models import *
from django.template.loader import render_to_string
from django.forms.fields import EMPTY_VALUES
from django.utils.translation import ugettext as _


class ResultForm(forms.Form):
    results = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=ATTEMPT_STATUS, required=False)

class ProjectTypeForm(forms.Form):
    options = ProjectType.objects.all().values_list('name', 'name')
    types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=options, required=False)

class RangeWidget(forms.MultiWidget):
    def __init__(self, widget, *args, **kwargs):
        widgets = (widget, widget)

        super(RangeWidget, self).__init__(widgets=widgets, *args, **kwargs)

    def decompress(self, value):
        return value

    def format_output(self, rendered_widgets):
        return '<div>' + ' - '.join(rendered_widgets) + '</div>'

class RangeField(forms.MultiValueField):
    default_error_messages = {
        'invalid_start': _(u'Enter a valid start value.'),
        'invalid_end': _(u'Enter a valid end value.'),
    }

    def __init__(self, field_class, widget=forms.TextInput(attrs = {'class': 'input-sm', 'style': 'width: 60px'}), *args, **kwargs):
        if not 'initial' in kwargs:
            kwargs['initial'] = ['','']

        fields = (field_class(), field_class())

        super(RangeField, self).__init__(
                fields=fields,
                widget=RangeWidget(widget),
                *args, **kwargs
                )

    def compress(self, data_list):
        if data_list:
            return [self.fields[0].clean(data_list[0]),self.fields[1].clean(data_list[1])]

        return None

class StatisticsForm(forms.Form):
    num_tables = RangeField(forms.IntegerField, required = False, label = '# of Tables')
    num_indexes = RangeField(forms.IntegerField, required = False, label = '# of Indexes')
    num_foreignkeys = RangeField(forms.IntegerField, required = False, label = '# of Foreign Keys')