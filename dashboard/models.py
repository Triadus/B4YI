# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timedelta

from django.core.validators import MinValueValidator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

User._meta.get_field('email')._unique = True


# Модель выбора валют
class Currency(models.Model):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=5)
    currency_image = models.ImageField(upload_to='currency_images/', blank=True, null=True)

    def __str__(self):
        return self.code


# Модель курса валют
class ExchangeRate(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_change = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    percent_change_1h = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.currency} - {self.last_updated}'

    class Meta:
        ordering = ['-rate']


# Модель вида инвестиций
class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    daily_profit_percentage = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return self.name


# Модель кошелька пользователя
class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                  validators=[MinValueValidator(0)])
    last_replenishment = models.DateTimeField(null=True, blank=True)
    last_withdrawal = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'currency',)

    def __str__(self):
        return f'{self.user.username} {self.currency}'


# Модель инвестиции пользователя
class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment_plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    next_updated = models.DateTimeField(null=True, blank=True)
    days_passed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Investment ID: {self.investment_id}, Plan: {self.investment_plan}, Currency: {self.currency}'

    class Meta:
        ordering = ['-date_created']

    def activate_investment(self):
        self.is_active = True
        self.last_updated = timezone.now()
        self.next_updated = self.last_updated + timedelta(days=1)
        self.save()


# Модель информации о инвестиции
class InvestmentsInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.action} - Investment ID: {self.investment.investment_id}'

    class Meta:
        ordering = ['-date_created']


# Модель кошелька профита
class ProfitWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    def __str__(self):
        return f'{self.currency}'


# Модель транзакций кошелька профита
class ProfitTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, null=True, blank=True)
    profit_wallet = models.ForeignKey(ProfitWallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    date_received = models.DateTimeField(default=now)

    def __str__(self):
        return f'{self.user.username} - {self.amount}'


# Модель запроса на пополнение кошелька
class WalletReplenishmentRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=False)
    is_executed = models.BooleanField(default=False)
    date_requested = models.DateTimeField(default=timezone.now)
    date_executed = models.DateTimeField(null=True, blank=True)

    def mark_executed(self):
        self.is_executed = True
        self.date_executed = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        original_request = None
        if self.pk is not None:
            original_request = WalletReplenishmentRequest.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        if original_request is not None and original_request.amount != self.amount:
            # Обновляем транзакцию при изменении суммы запроса на пополнение кошелька
            try:
                transaction = Transaction.objects.get(user=self.user, transaction_type='replenishment',
                                                      currency=self.currency)
                transaction.amount = self.amount
                transaction.save()
            except Transaction.DoesNotExist:
                # Если транзакция не существует, создаем новую
                Transaction.objects.create(
                    user=self.user,
                    transaction_type='replenishment',
                    currency=self.currency,
                    amount=self.amount
                )

    def __str__(self):
        return f'{self.user.username} - {self.amount} - {self.currency}'


# Модель запроса на вывод из кошелька
class WalletWithdrawalRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=False)
    is_executed = models.BooleanField(default=False)
    date_requested = models.DateTimeField(default=timezone.now)
    date_executed = models.DateTimeField(null=True, blank=True)

    def mark_executed(self):
        self.is_executed = True
        self.date_executed = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        original_request = None
        if self.pk is not None:
            original_request = WalletWithdrawalRequest.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        if original_request is not None and original_request.amount != self.amount:
            # Обновляем транзакцию при изменении суммы запроса на вывод средств
            try:
                transaction = Transaction.objects.get(user=self.user, transaction_type='withdrawal',
                                                      currency=self.currency)
                transaction.amount = self.amount
                transaction.save()
            except Transaction.DoesNotExist:
                # Если транзакция не существует, создаем новую
                Transaction.objects.create(
                    user=self.user,
                    transaction_type='withdrawal',
                    currency=self.currency,
                    amount=self.amount
                )

    def __str__(self):
        return f'{self.user.username} - {self.amount} - {self.currency}'


# Модель транзакции
class Transaction(models.Model):
    id = models.CharField(max_length=15, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=100, null=True, choices=(
        ('replenishment', _('Replenishment')),
        ('withdrawal', _('Withdrawal'))
    ))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100, default='pending', choices=(
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled'))
    ))
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_created']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = "#B4Y#" + str(uuid.uuid4().hex[:7]).upper()
        super().save(*args, **kwargs)

    def mark_completed(self):
        self.status = 'completed'
        self.save()

    def mark_cancelled(self):
        self.status = 'cancelled'
        self.save()

    def __str__(self):
        return f"Transaction ID: {self.id}, Type: {self.transaction_type}, Status: {self.status}"
