# -*- coding: utf-8 -*-
from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html

from .models import Wallet, Currency, ProfitWallet, InvestmentPlan, WalletReplenishmentRequest, WalletWithdrawalRequest, \
    Transaction, ExchangeRate, Investment, ProfitTransaction, InvestmentsInfo
from .tasks import update_exchange_rates, calculate_profit

admin.site.site_header = 'B4YI ADMIN-PANEL'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'balance', 'last_replenishment', 'last_withdrawal')
    list_filter = ('user', 'currency')
    search_fields = ('user__username', 'currency__code')
    list_editable = ('balance',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'image_tag',)

    def image_tag(self, obj):
        if obj.currency_image:
            return format_html('<img src="%s" width="22" height="22" />' % obj.currency_image.url)

    image_tag.short_description = 'Currency Image'
    image_tag.allow_tags = True

    fields = ('name', 'code', 'currency_image', 'image_tag',)
    readonly_fields = ('image_tag',)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['currency', 'rate', 'percent_change_1h', 'last_updated']
    actions = ['update_rates']
    actions_selection_counter = True

    def update_rates(self, request, queryset):
        update_exchange_rates()
        self.message_user(request, 'Rates updated successfully.')

    update_rates.short_description = 'Update rates'


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'daily_profit_percentage')


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'investment_plan', 'currency', 'amount', 'is_active', 'days_passed', 'date_created', 'last_updated',
        'next_updated')
    ordering = ('-date_created',)
    search_fields = ('user__username',)
    actions = ['calculate_profit']

    def calculate_profit(self, request, queryset):
        success = calculate_profit()

        if success:
            self.message_user(request, 'Profit updated successfully.')
        else:
            self.message_user(request, 'Profit update failed.', level=messages.ERROR)

    calculate_profit.short_description = 'Calculate profit'


@admin.register(InvestmentsInfo)
class InvestmentsInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment', 'action', 'date_created')


@admin.register(ProfitWallet)
class ProfitWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'balance')
    list_filter = ('user', 'currency')
    search_fields = ('user__username',)


@admin.register(ProfitTransaction)
class ProfitTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment', 'profit_wallet', 'amount', 'date_received')
    list_filter = ('user', 'investment', 'profit_wallet')
    search_fields = ('user__username', 'investment__user__username')
    readonly_fields = ['investment_link']

    def investment_link(self, obj):
        if obj.investment:
            return obj.investment
        return None

    investment_link.short_description = 'Investment'
    investment_link.admin_order_field = 'investment__id'

    def has_delete_permission(self, request, obj=None):
        return not obj or not obj.investment


# Запрос на пополнение
@admin.register(WalletReplenishmentRequest)
class WalletReplenishmentRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'date_requested', 'is_approved', 'is_executed', 'date_executed']
    actions = ['execute_replenishment']

    def execute_replenishment(self, request, queryset):
        for replenishment_request in queryset:
            if replenishment_request.is_approved:

                if not replenishment_request.is_executed:

                    try:
                        transaction = Transaction.objects.filter(user=replenishment_request.user,
                                                                 currency=replenishment_request.currency,
                                                                 transaction_type='replenishment',
                                                                 status='pending').latest('date_created')
                        # Используем latest('date_created') для получения последней созданной транзакции
                        transaction.mark_completed()
                    except ObjectDoesNotExist:
                        # Если нет транзакции с указанными параметрами, создаем новую
                        Transaction.objects.create(
                            user=replenishment_request.user,
                            transaction_type='replenishment',
                            currency=replenishment_request.currency,
                            amount=replenishment_request.amount,
                            status='completed'
                        )

                    replenishment_request.mark_executed()

                    wallet, created = Wallet.objects.get_or_create(user=replenishment_request.user,
                                                                   currency=replenishment_request.currency)
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
                                                       'currency': replenishment_request.currency}),
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
    list_display = ['user', 'amount', 'currency', 'date_requested', 'is_approved', 'is_executed', 'date_executed']
    actions = ['approve_withdrawal']

    def approve_withdrawal(self, request, queryset):
        for withdrawal_request in queryset:
            if withdrawal_request.is_approved:
                if not withdrawal_request.is_executed:
                    wallet = Wallet.objects.get(user=withdrawal_request.user, currency=withdrawal_request.currency)
                    if wallet.balance >= withdrawal_request.amount:
                        wallet.balance -= withdrawal_request.amount
                        wallet.last_withdrawal = timezone.now()
                        wallet.save()

                        transaction = Transaction.objects.get(user=withdrawal_request.user,
                                                              currency=withdrawal_request.currency,
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
                                                           'currency': withdrawal_request.currency}),
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
    list_display = ['id', 'user', 'date_created', 'transaction_type', 'currency', 'amount', 'status']
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
