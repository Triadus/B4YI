# -*- coding: utf-8 -*-
from datetime import timedelta

from allauth.account.views import PasswordChangeView, PasswordSetView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import mail_admins
from django.db import models
from django.db.models import Sum, ExpressionWrapper, FloatField, F, Prefetch, Case, When, Value
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .forms import WalletReplenishmentRequestForm, WalletWithdrawalRequestForm, UserProfileForm
from .models import Wallet, WalletWithdrawalRequest, Transaction, ExchangeRate, UserProfile, ProfitWallet, \
    OwnerCoinAddress


@login_required
def get_chart_data(request):
    balance_datas = Wallet.objects.filter(user=request.user)
    chart_data = []
    coin_names = []
    for balance_data in balance_datas:
        exchange_rate = ExchangeRate.objects.get(coin=balance_data.coin)
        balance_data.usdt_equivalent = balance_data.balance * exchange_rate.rate
        coin_names.append(balance_data.coin.name)
        chart_data.append(float(balance_data.usdt_equivalent))
    chart_data_json = {
        'labels': coin_names,
        'series': chart_data
    }
    return JsonResponse(chart_data_json)


@login_required
def profit_chart_data(request):
    profits = ProfitWallet.objects.filter(user=request.user).order_by('date_created')
    profit_values = [float(profit.amount) for profit in profits]
    dates = [profit.date_created.strftime('%Y-%m-%d') for profit in profits]

    chart_data_json = {
        'labels': dates,
        'series': [profit_values],
    }

    return JsonResponse(chart_data_json)


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/dashboard.html'

    @staticmethod
    def get_user_profile(user):
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = None
        return user_profile

    def get_context_data(self):
        user = self.request.user
        wallets = Wallet.objects.filter(user=user).prefetch_related(
            Prefetch('coin__exchangerate_set', queryset=ExchangeRate.objects.all())
        )
        for wallet in wallets:
            exchange_rate = wallet.coin.exchangerate_set.first()
            wallet.usdt_equivalent = wallet.balance * (exchange_rate.rate if exchange_rate else 1)

        user_profile = UserProfile.objects.filter(user=user).first()

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        first_day_of_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)

        profits = ProfitWallet.objects.filter(user=user)

        aggregated_profits = profits.annotate(
            profit_today=Case(
                When(date_created__date=today, then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            ),
            profit_yesterday=Case(
                When(date_created__date=yesterday, then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            ),
            profit_current_month=Case(
                When(date_created__date__gte=first_day_of_month, date_created__date__lte=today, then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            ),
            profit_last_month=Case(
                When(date_created__date__gte=first_day_of_last_month, date_created__date__lte=last_day_of_last_month,
                     then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            ),
        ).aggregate(
            profit_today_total=Sum('profit_today'),
            profit_yesterday_total=Sum('profit_yesterday'),
            profit_current_month_total=Sum('profit_current_month'),
            profit_last_month_total=Sum('profit_last_month'),
            profit_all_time=Sum('amount')
        )

        profit_today = aggregated_profits['profit_today_total'] or 0
        profit_yesterday = aggregated_profits['profit_yesterday_total'] or 0
        profit_current_month = aggregated_profits['profit_current_month_total'] or 0
        profit_last_month = aggregated_profits['profit_last_month_total'] or 0
        profit_all_time = aggregated_profits['profit_all_time'] or 0

        if profit_yesterday != 0:
            profit_day_change_percentage = ((profit_today - profit_yesterday) / profit_yesterday) * 100
        else:
            profit_day_change_percentage = 0

        if profit_last_month != 0:
            profit_month_change_percentage = ((profit_current_month - profit_last_month) / profit_last_month) * 100
        else:
            profit_month_change_percentage = 0

        context = {
            'wallets': wallets,
            'user_profile': user_profile,
            'user_profile_form': UserProfileForm(instance=user_profile),
            'profit_today': profit_today,
            'profit_yesterday': profit_yesterday,
            'profit_current_month': profit_current_month,
            'profit_last_month': profit_last_month,
            'profit_all_time': profit_all_time,
            'profit_month_change_percentage': profit_month_change_percentage,
            'profit_day_change_percentage': profit_day_change_percentage,
        }
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    @staticmethod
    def post(request):
        user = request.user
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_profile_form.is_valid():
            user_profile_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
        else:
            messages.error(request, 'Failed to update your profile. Please check the form.')

        return redirect('dashboard')


class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('dashboard')


class MyPasswordSetView(LoginRequiredMixin, PasswordSetView):
    success_url = reverse_lazy('dashboard')


#
# Запрос на пополнение
class WalletReplenishmentRequestView(LoginRequiredMixin, View):
    def get(self, request):
        form = WalletReplenishmentRequestForm()
        networks = OwnerCoinAddress.objects.all()

        context = {
            'form': form,
            'networks': networks,
        }

        return render(request, 'wallet/replenishment.html', context)

    def post(self, request):
        form = WalletReplenishmentRequestForm(request.POST)
        if form.is_valid():
            replenishment_request = form.save(commit=False)
            replenishment_request.user = request.user
            replenishment_request.save()

            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='replenishment',
                coin=replenishment_request.coin,
                network=replenishment_request.network,
                amount=replenishment_request.amount,
                txid=replenishment_request.txid,
            )

            mail_admins(
                subject='Запрос на пополнение',
                message=f'{request.user.username} {replenishment_request.amount} {replenishment_request.coin} ({replenishment_request.network})',
                fail_silently=False
            )

            return redirect('replenishment_success')

        context = {
            'form': form,
        }

        return render(request, 'wallet/replenishment.html', context)


# Успешный запрос на пополнение
class ReplenishmentSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'wallet/replenishment_success.html')


class WalletWithdrawalRequestView(LoginRequiredMixin, View):
    def get(self, request):
        existing_request = WalletWithdrawalRequest.objects.filter(user=request.user, is_executed=False).first()
        if existing_request:
            messages.warning(request, 'You already have a withdrawal request.')
            return redirect('dashboard')

        form = WalletWithdrawalRequestForm()

        context = {
            'form': form,
        }

        return render(request, 'wallet/withdrawal.html', context)

    def post(self, request):

        form = WalletWithdrawalRequestForm(request.POST)
        if form.is_valid():
            withdrawal_request = form.save(commit=False)
            withdrawal_request.user = request.user

            wallet = Wallet.objects.get(user=request.user, coin=withdrawal_request.coin)
            if wallet.balance < withdrawal_request.amount:
                messages.error(request, 'Not enough funds in your wallet.')
                return redirect('withdrawal')

            withdrawal_request.save()

            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                coin=withdrawal_request.coin,
                network=withdrawal_request.network,
                amount=withdrawal_request.amount
            )

            mail_admins(
                subject='Запрос на вывод средств',
                message=f'{request.user.username} {withdrawal_request.amount} {withdrawal_request.coin} ({withdrawal_request.network})',
                fail_silently=False
            )
            return redirect('withdrawal_success')
        return render(request, 'wallet/withdrawal.html', {'form': form})


# Успешный запрос на вывод
class WithdrawalSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'wallet/withdrawal_success.html')


# Кошелек
class WalletView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'wallet/wallet.html'
    context_object_name = 'transactions'
    paginate_by = 10

    def get_queryset(self):
        user_transactions = super().get_queryset().filter(user=self.request.user).order_by(
            'date_created').select_related('coin')
        return user_transactions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        balance_datas = Wallet.objects.filter(user=self.request.user).select_related('coin')
        exchange_rates = ExchangeRate.objects.select_related('coin').filter()
        exchange_rate_mapping = {rate.coin_id: rate for rate in exchange_rates}

        for balance_data in balance_datas:
            exchange_rate = exchange_rate_mapping.get(balance_data.coin_id)
            if exchange_rate:
                balance_data.usdt_equivalent = balance_data.balance * exchange_rate.rate
            else:
                balance_data.usdt_equivalent = 0

        total_usdt_balance = balance_datas.annotate(
            usdt_equivalent=ExpressionWrapper(
                F('balance') * F('coin__exchangerate__rate'),
                output_field=FloatField()
            )
        ).aggregate(Sum('usdt_equivalent'))['usdt_equivalent__sum']

        user_transactions_replenishment = Transaction.objects.filter(
            user=self.request.user, transaction_type='replenishment', status='completed'
        )
        user_transactions_withdrawal = Transaction.objects.filter(
            user=self.request.user, transaction_type='withdrawal', status='completed'
        )

        total_usd_replenishment = user_transactions_replenishment.aggregate(
            total_replenishment=Sum(F('amount') * F('coin__exchangerate__rate'))
        )['total_replenishment'] or 0

        total_usd_withdrawal = user_transactions_withdrawal.aggregate(
            total_withdrawal=Sum(F('amount') * F('coin__exchangerate__rate'))
        )['total_withdrawal'] or 0

        try:
            user_profile = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            user_profile = None

        context.update({
            'user_profile': user_profile,
            'balance_datas': balance_datas,
            'total_usdt_balance': total_usdt_balance,
            'exchange_rates': exchange_rates,
            'total_usd_replenishment': total_usd_replenishment if total_usd_replenishment is not None else 0,
            'total_usd_withdrawal': total_usd_withdrawal if total_usd_withdrawal is not None else 0,
        })

        return context
