from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^$', views.analytics_detail, name='analytics_detail'),
]
