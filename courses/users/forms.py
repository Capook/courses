from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django.forms import EmailField, CharField, Textarea, PasswordInput
from django.utils.translation import gettext_lazy as _

from django.core.mail import EmailMessage

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    name = CharField(label='Name', max_length=255)
    message = CharField(widget=Textarea, label='Statement of interest', help_text='Please describe your interest in using Gradebird.  We will email you instructions if we approve your request.')

    field_order = ['name', 'message', 'email', 'password1']

    # email = EmailField(label='E-mail')
    # password1 = CharField(label='Password', widget=PasswordInput)

    def save(self, request):
        user = super(UserSignupForm, self).save(request)
        user.name = self.cleaned_data['name']
        #just sending a single email, but using bulk merge template from anymail documentation
        message = EmailMessage(
            from_email="no-reply@gradebird.com",
            # The message body and html_body come from the stored template.
            # (You can still use %recipient.___% fields in the subject:)
            subject="Signup request from %recipient.name%",
            to=[f"capook@gmail.com"]
        )
        message.template_id = 'Instructor Signup Request'  # name of template in our account
        # The substitution data is exactly the same as in the previous example:
        message.merge_data = {
            'capook@gmail.com': {'name': user.name, 'email': user.email, 'message': self.cleaned_data['message']},
        }
        message.merge_global_data = {
            'ship_date': "May 15"  # Anymail maps globals to all recipients
        }
        message.send()

        user.save()
        return user

    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
