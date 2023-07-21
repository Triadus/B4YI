# -*- coding: utf-8 -*-
from allauth.account.forms import LoginForm, ResetPasswordForm, SignupForm, ChangePasswordForm, ResetPasswordKeyForm, \
    SetPasswordForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from django import forms
from dashboard.models import WalletReplenishmentRequest, WalletWithdrawalRequest, InvestmentPlan, Currency


class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['login'].widget = forms.TextInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter Username', 'id': 'username'})
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter Password', 'id': 'password'})
        self.fields['remember'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})


class UserRegistrationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['email'].widget = forms.EmailInput(
            attrs={'class': 'form-control mb-1', 'placeholder': 'Enter Email', 'id': 'email'})
        self.fields['email'].label = "Email"
        self.fields['username'].widget = forms.TextInput(
            attrs={'class': 'form-control mb-1', 'placeholder': 'Enter Username', 'id': 'username1'})
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-1', 'placeholder': 'Enter Password', 'id': 'password1'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-1', 'placeholder': 'Enter Confirm Password', 'id': 'password2'})
        self.fields['password2'].label = "Confirm Password"


class PasswordChangeForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['oldpassword'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter currunt password', 'id': 'password3'})
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter new password', 'id': 'password4'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter confirm password', 'id': 'password5'})
        self.fields['password2'].label = "Confirm Password"


class PasswordResetForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.fields['email'].widget = forms.EmailInput(
            attrs={'class': 'form-control mb-2', 'placeholder': ' Enter Email', 'id': 'email1'})
        self.fields['email'].label = "Email"


class PasswordResetKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetKeyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter new password', 'id': 'password6'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-1', 'placeholder': 'Enter confirm password', 'id': 'password7'})
        self.fields['password2'].label = "Confirm Password"


class PasswordSetForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordSetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control mb-2', 'placeholder': 'Enter new password', 'id': 'password8'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter confirm password', 'id': 'password9'})
        self.fields['password2'].label = "Confirm Password"


# Форма для запроса пополнения кошелька
class WalletReplenishmentRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.fields['currency'].widget.attrs.update({'class': 'form-select'})

        self.helper.layout = Layout(
            Field('currency', css_class='form-select'),
            Field('amount', css_class='input-group bootstrap-touchspin bootstrap-touchspin-injected'),
            Submit('submit', 'Submit', css_class='waves-effect waves-light')
        )

    class Meta:
        model = WalletReplenishmentRequest
        fields = ['currency', 'amount']


# Форма для запроса на вывод из кошелька
class WalletWithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model = WalletWithdrawalRequest
        fields = ['currency', 'amount']


# Форма для выбора и активации инвестиционного плана
class InvestmentForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=InvestmentPlan.objects.all(), empty_label=None, to_field_name='id')
    currency = forms.ModelChoiceField(queryset=Currency.objects.all(), empty_label=None)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
