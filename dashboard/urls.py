from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import DashboardView, WalletReplenishmentRequestView, ReplenishmentSuccessView, WalletWithdrawalRequestView, \
    WithdrawalSuccessView, WalletView, profit_chart_data
from .views import get_chart_data

urlpatterns = [

    path('', DashboardView.as_view(), name='dashboard'),

    path('replenishment/', WalletReplenishmentRequestView.as_view(), name='replenishment'),
    path('replenishment/success/', ReplenishmentSuccessView.as_view(), name='replenishment_success'),
    path('withdrawal/', WalletWithdrawalRequestView.as_view(), name='withdrawal'),
    path('withdrawal/success/', WithdrawalSuccessView.as_view(), name='withdrawal_success'),

    path('wallet/', WalletView.as_view(), name='wallet'),
    path('get_chart_data/', get_chart_data, name='get_chart_data'),
    path('profit_chart_data/', profit_chart_data, name='profit_chart_data'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
