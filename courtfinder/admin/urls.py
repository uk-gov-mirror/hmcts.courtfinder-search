from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
import views
from views import *

urlpatterns = [
    url(r'^auth/', include('django.contrib.auth.urls')),
    url(r'^courts$', views.courts, name='courts'),
    url(r'^court/(?P<id>[0-9]+)$', views.edit_court, name='court'),
    url(r'^court/(?P<id>[0-9]+)/address$', views.edit_address, name='address'),
    url(r'^court/(?P<id>[0-9]+)/address/(?P<address_id>[0-9]+)$', views.edit_address, name='address'),
    url(r'^court/(?P<id>[0-9]+)/delete_address/(?P<address_id>[0-9]+)$', views.delete_address, name='delete_address'),
    url(r'^court/(?P<id>[0-9]+)/contact$', ContactFormView.as_view(), name='contact'),
    url(r'^court/(?P<id>[0-9]+)/reorder_contacts', ContactReorderView.as_view(), name='reorder_contacts'),
    url(r'^court/(?P<id>[0-9]+)/email$', EmailFormView.as_view(), name='email'),
    url(r'^court/(?P<id>[0-9]+)/reorder_emails', EmailReorderView.as_view(), name='reorder_emails'),
    url(r'^users$', views.users, name='users'),
    url(r'^users/new$', views.add_user, name='add_user'),
    url(r'^account', views.account, name='account'),
    url(r'^$', RedirectView.as_view(pattern_name=settings.LOGIN_REDIRECT_URL))
]


