# -*- coding: utf-8 -*-

from _decimal import Decimal
from allauth.account.views import PasswordChangeView, PasswordSetView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import mail_admins
from django.db.models import Sum, ExpressionWrapper, FloatField, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View

from .forms import WalletReplenishmentRequestForm, WalletWithdrawalRequestForm, InvestmentForm
from .models import Wallet, WalletWithdrawalRequest, Transaction, ExchangeRate, Investment, InvestmentPlan, Currency, \
    InvestmentsInfo


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        wallets = Wallet.objects.filter(user=user).select_related('currency')

        # exchange_rates = ExchangeRate.objects.all().select_related('currency')# метод для уменьшения кол-ва запросов в базу данных

        for wallet in wallets:
            exchange_rate = ExchangeRate.objects.get(currency=wallet.currency)
            wallet.usdt_equivalent = wallet.balance * exchange_rate.rate

        context = {
            'wallets': wallets,
            # 'exchange_rates': exchange_rates,
        }

        return render(request, 'dashboard/dashboard.html', context)


class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('dashboard')


class MyPasswordSetView(LoginRequiredMixin, PasswordSetView):
    success_url = reverse_lazy('dashboard')


#
# Запрос на пополнение
class WalletReplenishmentRequestView(LoginRequiredMixin, View):
    def get(self, request):
        form = WalletReplenishmentRequestForm()
        return render(request, 'wallet/replenishment.html', {'form': form})

    def post(self, request):
        form = WalletReplenishmentRequestForm(request.POST)
        if form.is_valid():
            replenishment_request = form.save(commit=False)
            replenishment_request.user = request.user
            replenishment_request.save()

            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='replenishment',
                currency=replenishment_request.currency,
                amount=replenishment_request.amount
            )

            mail_admins(
                subject='Запрос на пополнение',
                message=f'{request.user.username} {replenishment_request.amount} {replenishment_request.currency}',
                fail_silently=False
            )
            return redirect('replenishment_success')
        return render(request, 'wallet/replenishment.html', {'form': form})


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
        return render(request, 'wallet/withdrawal.html', {'form': form})

    def post(self, request):

        form = WalletWithdrawalRequestForm(request.POST)
        if form.is_valid():
            withdrawal_request = form.save(commit=False)
            withdrawal_request.user = request.user

            wallet = Wallet.objects.get(user=request.user, currency=withdrawal_request.currency)
            if wallet.balance < withdrawal_request.amount:
                messages.error(request, 'Not enough funds in your wallet.')
                return redirect('withdrawal')

            withdrawal_request.save()

            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                currency=withdrawal_request.currency,
                amount=withdrawal_request.amount
            )

            mail_admins(
                subject='Запрос на вывод средств',
                message=f'{request.user.username} {withdrawal_request.amount} {withdrawal_request.currency}',
                fail_silently=False
            )
            return redirect('withdrawal_success')
        return render(request, 'wallet/withdrawal.html', {'form': form})


# Успешный запрос на вывод
class WithdrawalSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'wallet/withdrawal_success.html')


# Кошелек

class WalletView(LoginRequiredMixin, View):

    def get(self, request):
        user_transactions = Transaction.objects.filter(user=request.user).order_by('date_created').select_related(
            'currency')
        balance_datas = Wallet.objects.filter(user=request.user).select_related('currency')
        exchange_rates = ExchangeRate.objects.all().select_related('currency')

        for balance_data in balance_datas:
            exchange_rate = ExchangeRate.objects.select_related('currency').get(currency=balance_data.currency)
            balance_data.usdt_equivalent = balance_data.balance * exchange_rate.rate

        total_usdt_balance = balance_datas.annotate(
            usdt_equivalent=ExpressionWrapper(
                F('balance') * F('currency__exchangerate__rate'),
                output_field=FloatField()
            )
        ).aggregate(Sum('usdt_equivalent'))['usdt_equivalent__sum']

        total_usd_replenishment = Transaction.objects.filter(transaction_type='replenishment', status='completed') \
            .aggregate(total_replenishment=Sum(F('amount') * F('currency__exchangerate__rate'))) \
            .get('total_replenishment', 0)

        total_usd_withdrawal = Transaction.objects.filter(transaction_type='withdrawal', status='completed') \
            .aggregate(total_withdrawal=Sum(F('amount') * F('currency__exchangerate__rate'))) \
            .get('total_withdrawal', 0)

        if total_usd_withdrawal is None:
            total_usd_withdrawal = 0

        context = {
            'transactions': user_transactions,
            'balance_datas': balance_datas,
            'total_usdt_balance': total_usdt_balance,
            'exchange_rates': exchange_rates,
            'total_usd_replenishment': total_usd_replenishment,
            'total_usd_withdrawal': total_usd_withdrawal,
        }

        return render(request, 'wallet/wallet.html', context)


@login_required
def get_chart_data(request):
    balance_datas = Wallet.objects.filter(user=request.user)

    chart_data = []
    currency_names = []

    for balance_data in balance_datas:
        exchange_rate = ExchangeRate.objects.get(currency=balance_data.currency)
        balance_data.usdt_equivalent = balance_data.balance * exchange_rate.rate
        currency_names.append(balance_data.currency.name)
        chart_data.append(float(balance_data.usdt_equivalent))

    chart_data_json = {
        'labels': currency_names,
        'series': chart_data
    }

    return JsonResponse(chart_data_json)


class InvestmentView(LoginRequiredMixin, View):
    def get(self, request):
        investment_plans = InvestmentPlan.objects.all()
        form = InvestmentForm()
        selected_plan = None
        active_investments = Investment.objects.filter(user=request.user, is_active=True)

        context = {
            'investment_plans': investment_plans,
            'form': form,
            'selected_plan': selected_plan,
            'active_investments': active_investments
        }
        return render(request, 'investment/investment.html', context)

    def post(self, request):
        form = InvestmentForm(request.POST)
        if form.is_valid():
            plan_id = form.cleaned_data['plan'].id
            currency_id = form.cleaned_data['currency'].id
            amount = form.cleaned_data['amount']
            investment_plan = InvestmentPlan.objects.get(id=plan_id)
            currency = Currency.objects.get(id=currency_id)

            try:
                wallet = Wallet.objects.get(user=request.user, currency=currency)
            except Wallet.DoesNotExist:
                messages.error(request, f'You do not have a {currency.code} wallet.')
                return redirect('investment')

            if wallet.balance < amount:
                messages.error(request, 'Not enough funds in your wallet.')
                return redirect('investment')

            wallet.balance -= amount
            wallet.save()

            investment = Investment(user=request.user, investment_plan=investment_plan, currency=currency,
                                    amount=amount)
            investment.activate_investment()
            investment.save()

            InvestmentsInfo.objects.create(
                user=request.user,
                investment=investment,
                action='created'
            )

            return redirect('investment')
        else:
            investment_plans = InvestmentPlan.objects.all()
            selected_plan_id = request.POST.get('selected_plan')
            selected_plan = InvestmentPlan.objects.get(id=selected_plan_id) if selected_plan_id else None
            active_investments = Investment.objects.filter(user=request.user, is_active=True)

            context = {
                'investment_plans': investment_plans,
                'form': form,
                'selected_plan': selected_plan,
                'active_investments': active_investments
            }
            return render(request, 'investment/investment.html', context)


class CancelInvestmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        investment = get_object_or_404(Investment, pk=pk, user=request.user, is_active=True)

        try:
            wallet = Wallet.objects.get(user=request.user, currency=investment.currency)
        except Wallet.DoesNotExist:
            messages.error(request, f'You do not have a {investment.currency.code} wallet.')
            return redirect('investment')

        wallet.balance += investment.amount
        wallet.save()

        InvestmentsInfo.objects.create(user=request.user, investment=investment, action='deleted')
        investment.is_active = False
        investment.save()

        messages.success(request, 'Investment canceled successfully.')
        return redirect('investment')


class AddFundsView(LoginRequiredMixin, View):
    def post(self, request, pk):
        investment = get_object_or_404(Investment, pk=pk, user=request.user, is_active=True)
        amount = Decimal(request.POST.get('amount', 0))
        if amount <= 0:
            messages.error(request, 'Invalid amount.')
            return redirect('investment')

        try:
            wallet = Wallet.objects.get(user=request.user, currency=investment.currency)
        except Wallet.DoesNotExist:
            messages.error(request, f'You do not have a {investment.currency.code} wallet.')
            return redirect('investment')

        if wallet.balance < amount:
            messages.error(request, 'Not enough funds in your wallet.')
            return redirect('investment')

        wallet.balance -= amount
        wallet.save()

        investment.amount += amount
        investment.save()

        InvestmentsInfo.objects.create(user=request.user, investment=investment, action='funds_added')

        messages.success(request, 'Funds added to investment successfully.')
        return redirect('investment')
