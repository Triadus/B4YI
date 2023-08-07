# -*- coding: utf-8 -*-
from _decimal import Decimal

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html

from .models import Wallet, Coin, ProfitWallet, WalletReplenishmentRequest, WalletWithdrawalRequest, Transaction, \
    ExchangeRate, UserProfile, DayProfit, CoinAddress, TotalWallet, OwnersWallet
from .tasks import update_exchange_rates, calculate_total_balance, calc_user_percent_dep, calculate_user_profit

admin.site.site_header = 'B4YI ADMIN-PANEL'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'coin', 'balance', 'percentage_of_total_balance', 'last_replenishment', 'last_withdrawal')
    list_filter = ('user', 'coin')
    search_fields = ('user__username', 'coin__code')
    list_editable = ('balance',)
    actions = ['calc_user_percent_dep']

    def calc_user_percent_dep(self, request, queryset):
        calc_user_percent_dep()
        self.message_user(request, 'Update of user percentage of total balance success.')

    calc_user_percent_dep.short_description = 'Update percentage of total balance'


@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'image_tag',)

    def image_tag(self, obj):
        if obj.coin_image:
            return format_html('<img src="%s" width="22" height="22" />' % obj.coin_image.url)

    image_tag.short_description = 'Coin image'
    image_tag.allow_tags = True

    fields = ('name', 'code', 'coin_image', 'image_tag', 'is_active',)
    readonly_fields = ('image_tag',)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['coin', 'rate', 'percent_change_1h', 'last_updated']
    actions = ['update_rates']

    def update_rates(self, request, queryset):
        update_exchange_rates()
        self.message_user(request, 'Rates updated successfully.')

    update_rates.short_description = 'Update rates'


@admin.register(ProfitWallet)
class ProfitWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'coin', 'amount', 'date_created')
    list_filter = ('user', 'coin')
    search_fields = ('user__username',)
    actions = ['calculate_user_profit_action']

    def calculate_user_profit_action(self, request, queryset):
        calculate_user_profit()
        self.message_user(request, 'Calculation success')

    calculate_user_profit_action.short_description = 'Calculate user profit'


# Запрос на пополнение
@admin.register(WalletReplenishmentRequest)
class WalletReplenishmentRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'coin', 'date_requested', 'is_approved', 'is_executed', 'date_executed']
    actions = ['execute_replenishment']

    def execute_replenishment(self, request, queryset):
        for replenishment_request in queryset:
            if replenishment_request.is_approved:

                if not replenishment_request.is_executed:

                    try:
                        transaction = Transaction.objects.filter(user=replenishment_request.user,
                                                                 coin=replenishment_request.coin,
                                                                 transaction_type='replenishment',
                                                                 status='pending').latest('date_created')
                        # Используем latest('date_created') для получения последней созданной транзакции
                        transaction.mark_completed()
                    except ObjectDoesNotExist:
                        # Если нет транзакции с указанными параметрами, создаем новую
                        Transaction.objects.create(
                            user=replenishment_request.user,
                            transaction_type='replenishment',
                            coin=replenishment_request.coin,
                            amount=replenishment_request.amount,
                            status='completed'
                        )

                    replenishment_request.mark_executed()

                    wallet, created = Wallet.objects.get_or_create(user=replenishment_request.user,
                                                                   coin=replenishment_request.coin)
                    if created:
                        wallet.balance = 0
                    wallet.balance += replenishment_request.amount
                    wallet.last_replenishment = timezone.now()
                    wallet.save()

                    send_mail(
                        'Replenishment ',
                        '',
                        '',
                        [replenishment_request.user.email],
                        html_message=render_to_string('wallet/replenishment_email.html',
                                                      {'user': replenishment_request.user,
                                                       'amount': replenishment_request.amount,
                                                       'coin': replenishment_request.coin}),
                        fail_silently=False
                    )
                    self.message_user(request, 'Баланс успешно пополнен', level=messages.SUCCESS)
                else:
                    self.message_user(request, 'Ввод средств уже выполнен.', level=messages.ERROR)
            else:
                self.message_user(request, 'Запрос на пополнение баланса не подтвержден.', level=messages.ERROR)

    execute_replenishment.short_description = 'Execute wallet replenishment'


# Запрос на вывод средств
@admin.register(WalletWithdrawalRequest)
class WalletWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'coin', 'date_requested', 'is_approved', 'is_executed', 'date_executed']
    actions = ['approve_withdrawal']

    def approve_withdrawal(self, request, queryset):
        for withdrawal_request in queryset:
            if withdrawal_request.is_approved:
                if not withdrawal_request.is_executed:
                    wallet = Wallet.objects.get(user=withdrawal_request.user, coin=withdrawal_request.coin)
                    if wallet.balance >= withdrawal_request.amount:
                        wallet.balance -= withdrawal_request.amount
                        wallet.last_withdrawal = timezone.now()
                        wallet.save()

                        transaction = Transaction.objects.get(user=withdrawal_request.user,
                                                              coin=withdrawal_request.coin,
                                                              transaction_type='withdrawal', status='pending')
                        transaction.mark_completed()

                        withdrawal_request.mark_executed()
                        send_mail(
                            'Withdrawals',  # тема письма
                            '',  # текст письма из файла
                            '',
                            [withdrawal_request.user.email],
                            html_message=render_to_string('wallet/withdrawal_email.html',
                                                          {'user': withdrawal_request.user,
                                                           'amount': withdrawal_request.amount,
                                                           'coin': withdrawal_request.coin}),
                            fail_silently=False
                        )
                        self.message_user(request, 'Средства успешно выведены.', level=messages.SUCCESS)
                    else:
                        self.message_user(request, 'Недостаточно средств для вывода.', level=messages.ERROR)
                else:
                    self.message_user(request, 'Вывод средств уже выполнен.', level=messages.ERROR)
            else:
                self.message_user(request, 'Запрос на вывод средств не подтвержден.', level=messages.ERROR)

    approve_withdrawal.short_description = 'Approve wallet withdrawal'


# Создание транзакции
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date_created', 'transaction_type', 'coin', 'amount', 'status']
    list_filter = ['transaction_type', 'status']
    search_fields = ['id']
    ordering = ('-date_created',)
    actions = ['mark_completed', 'mark_cancelled']

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')

    mark_completed.short_description = 'Mark selected transactions as completed'

    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')

    mark_cancelled.short_description = 'Mark selected transactions as cancelled'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', ]


@admin.register(CoinAddress)
class CoinAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'coin', 'network', 'address']


@admin.register(DayProfit)
class DayProfitAdmin(admin.ModelAdmin):
    list_display = ['binance_pnl', 'profittrailer_pnl', 'date_created']


@admin.register(TotalWallet)
class TotalWalletAdmin(admin.ModelAdmin):
    list_display = (
    'coin', 'total_balance', 'total_balance_with_profit', 'relative_profit', 'users_profit', 'date_created')
    actions = ['calculate_total_balance']

    def total_balance_with_profit(self, obj):
        bot_profit = DayProfit.objects.latest('date_created').profittrailer_pnl
        total_balance = obj.total_balance
        total_balance_with_profit = bot_profit + total_balance

        obj.total_balance_with_profit = total_balance_with_profit
        obj.save()
        return total_balance_with_profit

    total_balance_with_profit.short_description = 'Total Balance with Profit'

    def calculate_total_balance(self, request, queryset):
        calculate_total_balance()
        self.message_user(request, 'Balance update success.')

    calculate_total_balance.short_description = 'Update balance'


@admin.register(OwnersWallet)
class OwnersWalletAdmin(admin.ModelAdmin):
    list_display = ['coin', 'balance', 'profit', 'percentage_of_total_balance', 'last_replenishment', 'last_withdrawal']
