from django.conf import settings
from django.conf.urls import include, url
from django.views.generic import TemplateView, RedirectView
from django.contrib import admin

from .. import views

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^_ver', views.VersionView.as_view(),name='_version'),
    url(r'^my/', include('apps.web.urls.my')),
    url(r'^profile/(?P<pk>\d+)$', views.UserDetailView.as_view(), name='user_details'),
    url(r'^competitions/', include('apps.web.urls.competitions', namespace="competitions")),
    url(r'^about/', TemplateView.as_view(template_name='web/help/about.html'), name='about'),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^health/', include('apps.health.urls')),
    url(r'^analytics/', include('apps.analytics.urls')),
    url(r'^forums/', include('apps.forums.urls')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^coopetitions/', include('apps.coopetitions.urls', namespace="coopetitions")),
    url(r'^queues/', include('apps.queues.urls', namespace="queues")),
    url(r'^customizer/', include('apps.customizer.urls')),
    url(r'^user_lookup/', views.user_lookup),

    # Third party
    url(r'^s3direct/', include('s3direct.urls')),

    # Direct URL redirects
    # In Django 1.9 these will no longer return as a permanent redirect by default. This seems fine for our case, as
    # these URLS could change in the future.

    url(r'^(?i)AutoML/?', RedirectView.as_view(url='https://www.codalab.org/competitions/2321')),
    url(r'^(?i)ChalearnLAP_Pose/?', RedirectView.as_view(url='https://www.codalab.org/competitions/2231')),
    url(r'^(?i)ChalearnLAP_Action/?', RedirectView.as_view(url='https://www.codalab.org/competitions/2241')),
    url(r'^(?i)Age/?', RedirectView.as_view(url='https://www.codalab.org/competitions/4711')),
    url(r'^(?i)Caption/?', RedirectView.as_view(url='https://www.codalab.org/competitions/3221')),

    # Static pages
    url(r'^(?i)highlights/?', TemplateView.as_view(template_name='web/highlights.html'), name="highlights"),

    # Helper that closes window upon visiting
    url(r'^close/$', TemplateView.as_view(template_name='close.html')),
]


if settings.DEBUG:
    '''
    Debugging email templates
    '''
    class ExtraContextTemplateView(TemplateView):
        extra_context = None

        def get(self, request, *args, **kwargs):
            if request.GET.get('text', None) is not None:
                # Allow text emails with ?text=1 in the request
                self.template_name = self.template_name.replace('.html', '.txt')
            return super(ExtraContextTemplateView, self).get(request, *args, **kwargs)

        def get_context_data(self, *args, **kwargs):
            context = super(ExtraContextTemplateView, self).get_context_data(**kwargs)
            if self.extra_context:
                context.update(self.extra_context)
            return context

    # urlpatterns += patterns('',
    #     (r'^email_view/organizer_to_participant/$', ExtraContextTemplateView.as_view(
    #         template_name='emails/notifications/participation_organizer_direct_email.html',
    #         extra_context={
    #             "body": "test",
    #             "competition": Competition.objects.first(),
    #             "site": Site.objects.get_current()
    #         }
    #     )),
    #     (r'^email_view/participation_requested/$', ExtraContextTemplateView.as_view(
    #         template_name='emails/notifications/participation_requested.html',
    #         extra_context={
    #             "competition": Competition.objects.first(),
    #             "site": Site.objects.get_current()
    #         }
    #     )),
    #     (r'^email_view/participation_revoked/$', ExtraContextTemplateView.as_view(
    #         template_name='emails/notifications/participation_revoked.html',
    #         extra_context={
    #             "competition": Competition.objects.first(),
    #             "site": Site.objects.get_current()
    #         }
    #     )),
    #     (r'^email_view/organizer_participation_requested/$', ExtraContextTemplateView.as_view(
    #         template_name='emails/notifications/organizer_participation_requested.html',
    #         extra_context={
    #             "competition": Competition.objects.first(),
    #             "site": Site.objects.get_current()
    #         }
    #     )),
    #     (r'^email_view/organizer_participation_revoked/$', ExtraContextTemplateView.as_view(
    #         template_name='emails/notifications/organizer_participation_revoked.html',
    #         extra_context={
    #             "competition": Competition.objects.first(),
    #             "site": Site.objects.get_current()
    #         }
    #     )),
    # )

    # Admin
    urlpatterns += [
        url(r'^admin/', include(admin.site.urls)),
    ]
