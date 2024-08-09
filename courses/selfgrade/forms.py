from django import forms

from .models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["initial_submission"]
        widgets = {
            "initial_submission": forms.ClearableFileInput(
                attrs={"accept": "application/pdf"},
            ),
        }
