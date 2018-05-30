from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^use_token/$', views.use_token, name='use_token'),
]
