from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

from dashboard.views import MyPasswordChangeView, MyPasswordSetView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboards View
    path('', include('dashboard.urls')),

    # Authorization
    path('account/', include('allauth.urls')),
    path('account-logout/', TemplateView.as_view(template_name="account/logout-success.html"), name='auth-logout'),
    path('account/password/change/', login_required(MyPasswordChangeView.as_view()), name="account_change_password"),
    path('account/password/set/', login_required(MyPasswordSetView.as_view()), name="account_set_password"),
]

if settings.DEBUG:
    urlpatterns = [path('__debug__/', include('debug_toolbar.urls')), ] + urlpatterns
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

