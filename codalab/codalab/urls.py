from apps.web.views import MyAdminView
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'', include('apps.web.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^clients/', include('apps.authenz.urls')),
    url(r'^api/', include('apps.api.routers')),
    url(r'^search/', include('haystack.urls')),
    url(r'^admin_monitoring_links/$', MyAdminView.as_view(), name='admin_monitoring_links'),
    url(r'^teams/', include('apps.teams.urls')),
    url(r'^newsletter/', include('apps.newsletter.urls', app_name='newsletter', namespace='newsletter')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^hidden-admin/', include(admin.site.urls)),

    url(r'^', include('pin_passcode.urls')),

    # Switch User
    url(r"^su/", include("django_switchuser.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
