from crispy_forms.templatetags.crispy_forms_field import css_class
from django import forms
from django.forms import inlineformset_factory
from django.forms import BaseInlineFormSet
from .models import Submission, GradedPart, Course, Material, Assignment, Part
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column, Div
from crispy_forms.layout import Layout, Submit


class HTML5DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class SubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.fields['initial_submission'].required = True
        self.fields['initial_submission'].help_text = 'PDF file of your assignment submission'
        self.fields['initial_submission'].label = ''

    class Meta:
        model = Submission
        fields = ["initial_submission","assignment","registration"]
        widgets = {
            "initial_submission": forms.FileInput(
                attrs={"accept": "application/pdf"},
            ),
            "assignment": forms.HiddenInput(),
            "registration": forms.HiddenInput()
        }

class GradedSubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GradedSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['graded_submission'].required = True
        self.fields['comments'].required = True
        #TODO it shows a "clear checkbox" for updating grading.  it doesnt' do anything.  not easy to remove.

    class Meta:
        model = Submission
        fields = ["graded_submission", "comments"]
        labels = {"graded_submission": 'Supporting annotations', "comments": 'Summary statement'}
        help_texts = {
            "graded_submission": 'Upload an annotated version of the same PDF you originally submitted for this assignment.  The annotations should be immediately visible--large and in a different color like red.  They should support your assessments entered above.',
            "comments": 'Provide a brief summary of how you did on this assignment.'
        }
        widgets = {
            "graded_submission": forms.ClearableFileInput(
                attrs={"accept": "application/pdf"},
            ),
            'comments': forms.Textarea(attrs={'rows': 4})
        }


class GradingInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(GradingInlineFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  # remove form tag (important)
            form.helper.layout = Layout(Field('self_grade', wrapper_class='nukemb3'))
            #it always adds mb3 to the wrapper.  this adds an additional class which is defined to overwrite mb3
            form.helper.render_hidden_fields = True #needed since we use layout!

            # it's a little crazy to do this every single time for every single part! Need to improve efficiency
            #if form.instance.id: #sometimes the form has no instance.  I don't know why.  ACtually I think it's only when there is ane rror id i missingand the form wont save

            schema = form.instance.part.schema
            choices = [('','---')] #empty string needed for html5 required attribute
            for item in schema.items.all():
                choices.append((item.points,item.name))

            form.fields['self_grade'] = forms.ChoiceField(choices=choices)
            form.fields['self_grade'].help_text = ''
            form.fields['self_grade'].widget.attrs['required'] = 'true'

GradingFormSet = inlineformset_factory(Submission, GradedPart, formset=GradingInlineFormSet,
                                       fields=['self_grade'],
                                       can_delete=False,
                                       extra=0)

#started writing this version with choices, but decided just to use the old one.  So this is incomplete and unused
class ReviewInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(ReviewInlineFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  # remove form tag (important)
            form.helper.layout = Layout(Field('grade', wrapper_class='nukemb3'))
            #it always adds mb3 to the wrapper.  this adds an additional class which is defined to overwrite mb3
            form.helper.render_hidden_fields = True #very important since layout would overwrite

            # it's a little crazy to do this every single time for every single part! Need to improve efficiency
            schema = form.instance.part.schema
            choices = [('','---')] #empty string needed for html5 required attribute
            for item in schema.items.all():
                choices.append((item.points,item.name))

            form.fields['grade'] = forms.ChoiceField(choices=choices)
            form.fields['grade'].help_text = ''
            form.fields['grade'].widget.attrs['required'] = 'true'

            # Don't use if form.instance.grade as it could be 0
            # NOTE: If user doesn't edit the initial, it will NOT be saved by default because django thinks it hasn't changed
            # I explicitly overrode the fields changed property in my form processing
            if form.instance.grade is None:
                form.initial['grade'] = form.instance.self_grade
            form.fields['grade'].widget.attrs['max'] = form.instance.points

#in use
class OldReviewInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(OldReviewInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.helper = FormHelper()
            form.helper.form_show_labels = False
            form.helper.form_tag = False  # VERY IMPORTANT
            form.fields['grade'].help_text = ''
            form.fields['grade'].widget.attrs['required'] = 'true'

            if form.instance.id:  # avoid erors in case the instance is fake - should not happen
                # fill in selfgrade as initial if it hasn't been reveiwed yet
                # Don't use if form.instance.grade as it could be 0
                # NOTE: If user doesn't edit the initial, it will NOT be saved by default because django thinks it hasn't changed
                # I explicitly overrode the fields changed property in my form processing
                if form.instance.grade is None:
                    form.initial['grade'] = form.instance.self_grade
                if form.instance.self_grade is None:
                    form.initial['grade'] = 0
                form.fields['grade'].widget.attrs['max'] = form.instance.points


ReviewFormSet = inlineformset_factory(Submission, GradedPart, formset=OldReviewInlineFormSet,
                                      fields=['grade'],
                                      can_delete=False,
                                      extra=0)



class PartFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = 'selfgrade/table_inline_formset_for_parts.html'
        self.layout = Layout(
            'name',  # Add your fields here
            'schema','rubric','DELETE'
        )
        self.form_tag = False

class PartInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(PartInlineFormSet, self).__init__(*args, **kwargs)
        self.helper = PartFormSetHelper()

PartFormSet = inlineformset_factory(Assignment, Part, formset=PartInlineFormSet,
                                    extra=21, #21 is a hardcode with the table template - do not modify
                                    fields=("name", "rubric", "schema"),
                                    labels={"rubric": "Special Instructions"},
                                    help_texts={"name": "", "rubric": "", "schema": ""},
                                    widgets={'rubric': forms.Textarea(attrs={'rows': 1})})

class ReviewerCommentsForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["reviewer_comments"]


class CourseNameForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name"]
        labels = {"name": ""}
        help_texts = {"name": ""}


class CourseDescriptionForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["description"]
        labels = {"description": ""}
        help_texts = {"description": ""}


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["name", "description", "file", "course"]
        widgets = {"course": forms.HiddenInput(), 'description': forms.Textarea(attrs={'rows': 4})}


class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout("course",  # need to include hidden input!
                                    Row(
                                        Column('name', css_class='form-group col-sm-12'),
                                        css_class='form-row'
                                    ),
                                    Row(
                                        Column("due_at", css_class='form-group col-sm-6'),
                                        Column("self_grades_due_at", css_class='form-group col-sm-6'),
                                        css_class='form-row'
                                    ),
                                    Row(
                                        Column("statement_pdf", css_class='form-group col-sm-6'),
                                        Column("solution_pdf", css_class='form-group col-sm-6'),
                                        css_class='form-row'
                                    ),
                                    )

    class Meta:
        model = Assignment
        fields = ["name",
                  # "description",
                  "due_at", "self_grades_due_at", "statement_pdf", "solution_pdf", "course"]
        # labels={"name":""}
        help_texts = {"name": "", "due_at": "", "self_grades_due_at": "", "statement_pdf": "", "solution_pdf": ""}
        widgets = {"course": forms.HiddenInput(),
                   "due_at": HTML5DateTimeInput(),
                   "self_grades_due_at": HTML5DateTimeInput(),
                   # 'description': forms.Textarea(attrs={'rows': 4})
                   "statement_pdf": forms.ClearableFileInput(
                       attrs={"accept": "application/pdf"},
                   ),
                   }



