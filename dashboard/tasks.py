# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
import requests
from _decimal import Decimal
from celery import shared_task
from django.utils import timezone

from .models import ProfitWallet, Currency, ExchangeRate, Investment, Wallet, ProfitTransaction
import coreapi


# @shared_task
# def update_profit_wallet():
#     api = coreapi.Client()
#     stats = api.get('http://195.181.240.210:10060//api/v2.5/data/stats?token=TjB6paqGspMA9ncWBzddEUhjy')
#     totalprofit = stats['basic']['totalProfit']
#
#     profit_wallet = ProfitWallet()
#     profit_wallet.balance = Decimal(totalprofit)
#     profit_wallet.bot = "PT-BOT"
#     profit_wallet.currency = "USDT"
#     profit_wallet.date_updated = datetime.now().date(),
#     profit_wallet.save()


@shared_task
def update_exchange_rates():
    response = requests.get('https://api.binance.com/api/v3/ticker/24hr')
    data = response.json()

    for item in data:
        symbol = item['symbol']
        price = item['lastPrice']
        price_change = item['priceChange']
        percent_change_1h = item['priceChangePercent']
        usdt_code = 'USDT'

        if symbol.endswith(usdt_code):
            currency_code = symbol[:-len(usdt_code)]

            try:
                currency = Currency.objects.get(code=currency_code)
            except Currency.DoesNotExist:
                continue

            exchange_rate, created = ExchangeRate.objects.get_or_create(currency=currency)
            exchange_rate.rate = price
            exchange_rate.price_change = price_change
            exchange_rate.percent_change_1h = percent_change_1h
            exchange_rate.last_updated = timezone.now()
            exchange_rate.save()


@shared_task
def calculate_profit():
    now = timezone.now()
    active_investments = Investment.objects.filter(is_active=True)
    success = False

    for investment in active_investments:
        time_passed = now - investment.last_updated

        if time_passed >= timedelta(minutes=1):
            profit_percentage = investment.investment_plan.daily_profit_percentage
            calculated_profit = investment.amount * (profit_percentage / 100)

            profit_wallet, created = ProfitWallet.objects.get_or_create(
                user=investment.user,
                currency=investment.currency,
                defaults={'balance': 0}
            )

            profit_wallet.balance += calculated_profit
            profit_wallet.save()

            transaction = ProfitTransaction.objects.create(
                user=investment.user,
                investment=investment,
                profit_wallet=profit_wallet,
                amount=calculated_profit,
                date_received=now
            )

            user_wallet = Wallet.objects.get(user=investment.user, currency=investment.currency)
            user_wallet.balance += calculated_profit
            user_wallet.save()

            investment.last_updated = now
            investment.next_updated = now + timedelta(minutes=1)
            investment.days_passed += 1
            investment.save()

            success = True

    return success

