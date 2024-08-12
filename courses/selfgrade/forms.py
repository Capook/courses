from django import forms
from django.forms import inlineformset_factory
from django.forms import BaseInlineFormSet
from .models import Submission, GradedPart
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row


class SubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(SubmissionForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['initial_submission'].required = True
        self.fields['initial_submission'].help_text = 'PDF file of your assignment submission'
        self.fields['initial_submission'].label = ''

    class Meta:
        model = Submission
        fields = ["initial_submission"]
        widgets = {
            "initial_submission": forms.ClearableFileInput(
                attrs={"accept": "application/pdf"},
            ),
        }

class GradedSubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(GradedSubmissionForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        #I want require filling graded submission if one wasn't already submitted...
        # but instance is not an actual database entry the way its done now
        #if not self.instance.graded_submission:
            #self.fields['graded_submission'].required = True

    class Meta:
        model = Submission
        fields = ["graded_submission"]
        widgets = {
            "graded_submission": forms.ClearableFileInput(
                attrs={"accept": "application/pdf"},
            ),
        }

class RequiredInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            #form.empty_permitted = False
            #form.use_required_attribute = True #not sure this does anything
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  #VERY IMPORTANT
            # form.helper.layout = Layout(
            #     Row(
            #         Field('self_grade'),
            #         style="margin-bottom: 0!important;"
            #     ),
            # )
            form.fields['self_grade'].help_text = ''
            form.fields['self_grade'].widget.attrs['required'] = 'true'
            if form.instance.points: #designed to avoid errors in case the instance is fake and there is no assignedpart.  not sure it works
                form.fields['self_grade'].widget.attrs['max'] = form.instance.points

    #with formsetfactory, it appears that form-level validation has to be done by hand.
    # sadly I can't get html5 validation this way.. done in javascript :/
    #I Don't want to make fields required in the db because the gradedPart items are created empty at submission time
    # def clean(self):
    #     super().clean()
    #
    #     for form in self.forms:
    #         if not form.cleaned_data:  # Skip empty forms
    #             continue
    #
    #         if not form.cleaned_data.get('self_grade'):
    #             form.add_error('self_grade', "This field is required.")

GradingFormSet = inlineformset_factory(Submission, GradedPart,formset=RequiredInlineFormSet,
                                       fields=['self_grade'],
                                       can_delete=False,
                                       extra=0) # Create a formset for GradedPartForm

