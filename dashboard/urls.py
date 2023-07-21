from django.urls import path
from .views import DashboardView, WalletReplenishmentRequestView, ReplenishmentSuccessView, WalletWithdrawalRequestView, \
    WithdrawalSuccessView, WalletView, InvestmentView, CancelInvestmentView, AddFundsView
from .views import get_chart_data

urlpatterns = [

    path('', DashboardView.as_view(), name='dashboard'),

    path('replenishment/', WalletReplenishmentRequestView.as_view(), name='replenishment'),
    path('replenishment/success/', ReplenishmentSuccessView.as_view(), name='replenishment_success'),
    path('withdrawal/', WalletWithdrawalRequestView.as_view(), name='withdrawal'),
    path('withdrawal/success/', WithdrawalSuccessView.as_view(), name='withdrawal_success'),

    path('wallet/', WalletView.as_view(), name='wallet'),
    path('get_chart_data/', get_chart_data, name='get_chart_data'),

    path('investment/', InvestmentView.as_view(), name='investment'),
    path('investment/<uuid:pk>/cancel/', CancelInvestmentView.as_view(), name='cancel_investment'),
    path('investment/<uuid:pk>/add-funds/', AddFundsView.as_view(), name='add_funds'),
]
