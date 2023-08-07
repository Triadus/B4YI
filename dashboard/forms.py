# -*- coding: utf-8 -*-
from allauth.account.forms import LoginForm, ResetPasswordForm, SignupForm, ChangePasswordForm, ResetPasswordKeyForm, \
    SetPasswordForm
from crispy_forms.helper import FormHelper
from django import forms
from django.core.validators import RegexValidator

from dashboard.models import WalletReplenishmentRequest, WalletWithdrawalRequest, UserProfile, CoinAddress, Coin


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

    # Фильтрация по статусу если валюта активна
    def __init__(self, *args, **kwargs):
        super(WalletReplenishmentRequestForm, self).__init__(*args, **kwargs)
        self.fields['coin'].queryset = Coin.objects.filter(is_active=True)

    class Meta:
        model = WalletReplenishmentRequest
        fields = ['coin', 'amount']


# Форма для запроса на вывод из кошелька
class WalletWithdrawalRequestForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(WalletWithdrawalRequestForm, self).__init__(*args, **kwargs)
        self.fields['coin'].queryset = Coin.objects.filter(is_active=True)

    class Meta:
        model = WalletWithdrawalRequest
        fields = ['coin', 'amount']


# Форма профиля пользователя
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'first_name', 'last_name', 'phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+999999999'}),
        }

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].validators.append(self.phone_regex)


class CoinAddressForm(forms.ModelForm):
    class Meta:
        model = CoinAddress
        fields = ['user', 'coin', 'address']
