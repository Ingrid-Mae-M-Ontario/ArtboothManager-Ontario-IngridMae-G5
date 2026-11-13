from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User


def add_bootstrap(form):
    for name, field in form.fields.items():
        css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
        field.widget.attrs['class'] = css


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'contact_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('email', 'first_name', 'last_name'):
            self.fields[name].required = True
        add_bootstrap(self)

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username or email'
        add_bootstrap(self)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'contact_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        add_bootstrap(self)

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email