from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^like/(?P<submission_pk>\d+)/', views.like, name='like'),
    url(r'^dislike/(?P<submission_pk>\d+)/', views.dislike, name='dislike'),
]
