import re

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _

from .models import Voter

ID_RE = re.compile(r"^[A-Za-z0-9/._-]{3,50}$")


class RegisterForm(forms.Form):
    full_name = forms.CharField(label=_("Full name"), max_length=150)
    student_id = forms.CharField(label=_("Student ID"), max_length=50)
    department = forms.CharField(label=_("Department"), max_length=100)
    year = forms.TypedChoiceField(
        label=_("Year"),
        choices=[("", "---")] + [(str(i), str(i)) for i in range(1, 8)],
        coerce=int,
    )
    rfid = forms.CharField(label=_("RFID card number"), max_length=64)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput)
    # Honeypot: real people never see or fill this field; simple bots do.
    website = forms.CharField(required=False)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(_("Registration failed."))
        return ""

    def clean_full_name(self):
        name = " ".join(self.cleaned_data["full_name"].split())
        if len(name.split()) < 2:
            raise forms.ValidationError(_("Please enter your full name (at least two names)."))
        return name

    def clean_department(self):
        return " ".join(self.cleaned_data["department"].split())

    def clean_student_id(self):
        sid = self.cleaned_data["student_id"].strip()
        if not ID_RE.match(sid):
            raise forms.ValidationError(
                _("Student ID may contain letters, numbers and / . _ - only (3 to 50 characters).")
            )
        if get_user_model().objects.filter(username__iexact=sid).exists():
            raise forms.ValidationError(_("This student ID is already registered."))
        return sid

    def clean_rfid(self):
        rfid = "".join(self.cleaned_data["rfid"].split()).upper()
        if not rfid:
            raise forms.ValidationError(_("This field is required."))
        if Voter.objects.filter(rfid_uid__iexact=rfid).exists():
            raise forms.ValidationError(_("This RFID card is already registered."))
        return rfid

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", _("The two passwords do not match."))
            else:
                try:
                    password_validation.validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        return cleaned
