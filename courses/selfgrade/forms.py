from django import forms
from django.forms import inlineformset_factory
from django.forms import BaseInlineFormSet
from .models import Submission, GradedPart
from crispy_forms.helper import FormHelper


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
        #I won't require filling graded submission if one wasn't already submitted...
        # but instance is not an actual database entry the way its done now, so it doesn't work.. just leave it required to be safe
        self.fields['graded_submission'].required = True

    class Meta:
        model = Submission
        fields = ["graded_submission"]
        labels = {"graded_submission":'Supporting annotations'}
        help_texts = {"graded_submission": 'Upload an annotated version of the same PDF you originally submitted for this assignment.  The annotations should be immediately visible--large and in a different color like red.  They should support your scores entered above.  Do not edit the PDF content; instead use annotations and upload here.'}
        widgets = {
            "graded_submission": forms.ClearableFileInput(
                attrs={"accept": "application/pdf"},
            ),
        }

class GradingInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(GradingInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  #VERY IMPORTANT
            form.fields['self_grade'].help_text = ''
            form.fields['self_grade'].widget.attrs['required'] = 'true'
            if form.instance.id: #avoid erors in case the instance is fake - should not happen
                form.fields['self_grade'].widget.attrs['max'] = form.instance.points

GradingFormSet = inlineformset_factory(Submission, GradedPart,formset=GradingInlineFormSet,
                                       fields=['self_grade'],
                                       can_delete=False,
                                       extra=0)

class ReviewInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(ReviewInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  #VERY IMPORTANT
            form.fields['grade'].help_text = ''
            form.fields['grade'].widget.attrs['required'] = 'true'

            if form.instance.id: #avoid erors in case the instance is fake - should not happen
                # fill in selfgrade as initial if it hasn't been reveiwed yet
                if not form.instance.grade:
                    form.initial['grade'] = form.instance.self_grade
                form.fields['grade'].widget.attrs['max'] = form.instance.points

ReviewFormSet = inlineformset_factory(Submission, GradedPart, formset=ReviewInlineFormSet,
                                       fields=['grade'],
                                       can_delete=False,
                                       extra=0)

class ReviewerCommentsForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["reviewer_comments"]
