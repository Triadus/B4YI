# -*- coding: utf-8 -*-
from _decimal import Decimal
import requests
from celery import shared_task
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import Coin, ExchangeRate, Wallet, TotalWallet, DayProfit, ProfitWallet, OwnersWallet


# Обновление курса монет
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
            coin_code = symbol[:-len(usdt_code)]

            try:
                coin = Coin.objects.get(code=coin_code)
            except Coin.DoesNotExist:
                continue

            exchange_rate, created = ExchangeRate.objects.get_or_create(coin=coin)
            exchange_rate.rate = price
            exchange_rate.price_change = price_change
            exchange_rate.percent_change_1h = percent_change_1h
            exchange_rate.last_updated = timezone.now()
            exchange_rate.save()


# Рассчет общего баланса
@shared_task
def calculate_total_balance():
    coins = Wallet.objects.values('coin').distinct()

    for coin in coins:
        coin_id = coin['coin']
        coin_instance = Coin.objects.get(pk=coin_id)
        total_balance = Wallet.objects.filter(coin_id=coin_id).aggregate(Sum('balance'))['balance__sum'] or Decimal(
            '0.00')
        owners_wallet = OwnersWallet.objects.filter(coin_id=coin_id).latest('last_replenishment')

        total_wallet = TotalWallet.objects.create(coin=coin_instance)
        total_wallet.total_balance = total_balance + owners_wallet.balance
        total_wallet.date_created = timezone.now()
        total_wallet.save()

        bot_profit = DayProfit.objects.latest('date_created').profittrailer_pnl
        total_balance = TotalWallet.objects.latest('date_created').total_balance
        total_balance_with_profit = bot_profit + total_balance

        total_wallet.total_balance_with_profit = total_balance_with_profit
        total_wallet.relative_profit = bot_profit / total_balance_with_profit * 100
        total_wallet.save()

    return 'Successfully calculated total balance.'


# Рассчет вклада пользователя относительно общего баланса
@shared_task
def calc_user_percent_dep():
    try:
        coins = Wallet.objects.values_list('coin', flat=True).distinct()

        for coin in coins:
            total_balance_obj = TotalWallet.objects.filter(coin=coin).latest('date_created')
            total_balance = total_balance_obj.total_balance or 0
            owners_wallet = OwnersWallet.objects.filter(coin=coin).latest('last_replenishment')
            owners_balance = owners_wallet.balance or 0

            if total_balance != 0:
                owners_percentage_of_total_balance = (owners_balance / total_balance) * 100
            else:
                owners_percentage_of_total_balance = 0
            owners_wallet.percentage_of_total_balance = owners_percentage_of_total_balance
            owners_wallet.save()

            wallets = Wallet.objects.filter(coin=coin)

            for wallet in wallets:
                user_balance = wallet.balance
                if total_balance != 0:
                    percentage_of_total_balance = (user_balance / total_balance) * 100
                else:
                    percentage_of_total_balance = 0
                wallet.percentage_of_total_balance = percentage_of_total_balance
                wallet.save()

        return 'Successfully updated percentage_of_total_balance for all users'
    except Exception as e:
        return f'An error occurred: {str(e)}'


# Рассчет профита
@shared_task
def calculate_user_profit():
    try:
        with transaction.atomic():
            coin_ids = Wallet.objects.values_list('coin', flat=True).distinct()
            print("Coins found:", coin_ids)  # Выведем список монет
            for coin_id in coin_ids:
                coin = Coin.objects.get(pk=coin_id)  # Получим экземпляр Coin по ID
                profittrailer_pnl = DayProfit.objects.latest('date_created').profittrailer_pnl
                print("Profittrailer_pnl for coin", coin, ":", profittrailer_pnl)  # Выведем pnl для каждой монеты
                wallets = Wallet.objects.filter(coin=coin)
                total_users_profit = Decimal(0)
                for wallet in wallets:
                    user_percentage = wallet.percentage_of_total_balance
                    user_profit = Decimal(user_percentage) * Decimal(profittrailer_pnl) * Decimal(0.66) / Decimal(100)
                    total_users_profit += user_profit
                    print("User profit for wallet", wallet, ":", user_profit)  # Выведем профит для каждого кошелька

                    profit_wallet = ProfitWallet.objects.create(
                        user=wallet.user,
                        coin=coin,  # Передаем экземпляр Coin
                        amount=user_profit,
                        date_created=timezone.now()
                    )

                    wallet.balance += user_profit
                    wallet.save()
                    print("New balance for wallet", wallet, ":", wallet.balance)  # Выведем новый баланс

                total_wallet = TotalWallet.objects.filter(coin=coin).latest('date_created')
                total_wallet.users_profit = total_users_profit
                total_wallet.save()

                # Получите существующий объект OwnersWallet для данной монеты
                existing_owners_wallet = OwnersWallet.objects.filter(coin=coin).latest('last_replenishment')

                # Создайте новый объект OwnersWallet, скопировав значения из существующего
                owners_wallet = OwnersWallet.objects.create(
                    coin=existing_owners_wallet.coin,
                    balance=existing_owners_wallet.balance,
                    profit=profittrailer_pnl - total_users_profit,
                    last_replenishment=timezone.now()
                )

                # Теперь добавьте прибыль к балансу
                owners_wallet.balance += owners_wallet.profit

                # И сохраните изменения
                owners_wallet.save()

            return 'Successfully'
    except Exception as e:
        print("An error occurred:", str(e))  # Выведем ошибку, если она есть
        return f'An error occurred: {str(e)}'
