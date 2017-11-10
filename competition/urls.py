from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<tour_name>[^/]+)/$', views.submit, name='submit'),
    url(r'^(?P<tour_name>[^/]+)/predictions/$', views.predictions, name='predictions'),
    url(r'^(?P<tour_name>[^/]+)/table/$', views.table, name='table'),
    url(r'^(?P<tour_name>[^/]+)/join/$', views.join, name='join'),
]
