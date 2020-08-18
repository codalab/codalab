from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.ConfigurationFormView.as_view(), name='customize_codalab'),
]
