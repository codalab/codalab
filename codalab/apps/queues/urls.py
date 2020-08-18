from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.QueueListView.as_view(), name='list'),
    url(r'^create$', views.QueueCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)$', views.QueueUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>\d+)$', views.QueueDeleteView.as_view(), name='delete'),
]
