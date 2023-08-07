# -*- coding: utf-8 -*-
import os
import uuid
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

User._meta.get_field('email')._unique = True


# Модель выбора валют
class Coin(models.Model):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=5)
    is_active = models.BooleanField(default=False)
    coin_image = models.ImageField(upload_to='coin_images/', blank=True, null=True)

    def __str__(self):
        return self.code


# Профиль пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        else:
            return 'images/users/user-dummy-img.jpg'

    def __str__(self):
        return f"{self.user.username}"


@receiver(pre_save, sender=UserProfile)
def delete_old_avatar(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_avatar = UserProfile.objects.get(pk=instance.pk).avatar
    except UserProfile.DoesNotExist:
        return False

    new_avatar = instance.avatar
    if old_avatar and old_avatar != new_avatar:
        if not new_avatar:
            os.remove(old_avatar.path)


@receiver(pre_delete, sender=UserProfile)
def delete_avatar_file(sender, instance, **kwargs):
    if instance.avatar and os.path.isfile(instance.avatar.path):
        os.remove(instance.avatar.path)


class CoinAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    NETWORK_CHOICES = (
        ('BSC', 'BNB Smart Chain (BEP20)'),
        ('ETH', 'Ethereum (ERC20)'),
        ('TRX', 'Tron (TRC20)'),
    )
    network = models.CharField(max_length=4, choices=NETWORK_CHOICES)
    address = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.coin.name} Coin Address"


# Модель курса валют
class ExchangeRate(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_change = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    percent_change_1h = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.coin} - {self.last_updated}'

    class Meta:
        ordering = ['-rate']
        verbose_name = 'Coin exchange rate'


# Модель кошелька пользователя
class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                  validators=[MinValueValidator(0)])
    percentage_of_total_balance = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    last_replenishment = models.DateTimeField(null=True, blank=True)
    last_withdrawal = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'coin',)
        verbose_name = 'User wallet'

    def __str__(self):
        return f'{self.user.username} {self.coin}'


# Общий портфель
class TotalWallet(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
    total_balance = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_balance_with_profit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    users_profit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    relative_profit = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name='Relative profit')
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Total Wallet'
        verbose_name_plural = 'Total Wallet'


class OwnersWallet(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    percentage_of_total_balance = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True,
                                                      verbose_name='Percentage of total balance')
    last_replenishment = models.DateTimeField(null=True, blank=True)
    last_withdrawal = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Owners Wallet'
        verbose_name_plural = 'Owners Wallet'


# Модель получения дневной прибыли
class DayProfit(models.Model):
    binance_pnl = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profittrailer_pnl = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    date_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Bot day profit'


# Модель кошелька профита
class ProfitWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    date_created = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.coin}: {self.amount}'

    class Meta:
        verbose_name = 'User profit'


# Модель запроса на пополнение кошелька
class WalletReplenishmentRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
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
            try:
                transaction = Transaction.objects.get(user=self.user, transaction_type='replenishment',
                                                      coin=self.coin)
                transaction.amount = self.amount
                transaction.save()
            except Transaction.DoesNotExist:
                Transaction.objects.create(
                    user=self.user,
                    transaction_type='replenishment',
                    coin=self.coin,
                    amount=self.amount
                )

    def __str__(self):
        return f'{self.user.username} - {self.amount} - {self.coin}'

    class Meta:
        verbose_name = 'Balance replenishment'


# Модель запроса на вывод из кошелька
class WalletWithdrawalRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
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
            try:
                transaction = Transaction.objects.get(user=self.user, transaction_type='withdrawal',
                                                      coin=self.coin)
                transaction.amount = self.amount
                transaction.save()
            except Transaction.DoesNotExist:
                Transaction.objects.create(
                    user=self.user,
                    transaction_type='withdrawal',
                    coin=self.coin,
                    amount=self.amount
                )

    def __str__(self):
        return f'{self.user.username} - {self.amount} - {self.coin}'

    class Meta:
        verbose_name = 'Balance withdrawal'


# Модель транзакции
class Transaction(models.Model):
    id = models.CharField(max_length=15, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=100, null=True, choices=(
        ('replenishment', _('Replenishment')),
        ('withdrawal', _('Withdrawal'))
    ))
    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100, default='pending', choices=(
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled'))
    ))
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_created']
        verbose_name = 'Balance transaction'

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
