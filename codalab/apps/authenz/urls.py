from django.conf.urls import include, url

from apps.authenz import views

def oauth2_include():
    """Expose a limited set of endpoints from oauth2_provider.urls."""
    urlconf, name, namespace = include('oauth2_provider.urls', namespace='oauth2_provider')
    urlconf.urlpatterns = [p for p in urlconf.urlpatterns if p.name == 'token']
    return (urlconf, name, namespace)

urlpatterns = [
    url(r'^validation', views.ValidationApi.as_view()),
    url(r'^info', views.InfoApi.as_view()),
    url(r'', oauth2_include()),
]
