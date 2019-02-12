"""test_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^competition/', include('competition.urls', namespace="competition")),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^register/$', views.signup, name='signup'),
    url(r'^register/activation_sent/$',
        TemplateView.as_view(
            template_name='registration/activation_sent.html'),
        name='activation_sent'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/', include('member.urls', namespace="member")),
    url(r'^about/', views.about, name='about'),

]
