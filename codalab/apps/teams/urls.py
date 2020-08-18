from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^(?P<competition_pk>\d+)/$', views.TeamDetailView.as_view(), name='team_detail'),
    url(r'^(?P<competition_pk>\d+)/create$', views.TeamCreateView.as_view(), name='team_new'),
    url(r'^(?P<competition_pk>\d+)/(?P<team_pk>\d+)/edit/$', views.TeamEditView.as_view(), name='team_edit'),
    url(r'^(?P<competition_pk>\d+)/(?P<team_pk>\d+)/delete/$', views.TeamCancelView.as_view(), name='team_delete'),
    url(r'^(?P<competition_pk>\d+)/(?P<request_pk>\d+)/(?P<action>accept|reject|cancel)/$', views.RequestTeamView.as_view(), name='team_request_action'),
    url(r'^(?P<competition_pk>\d+)/request/(?P<team_pk>\d+)/$', views.NewRequestTeamView.as_view(), name='team_enrol'),
    url(r'^(?P<competition_pk>\d+)/create_org_team/$', views.CompetitionOrganizerTeams.as_view(), name='create_org_team'),
    url(r'^(?P<competition_pk>\d+)/create_org_teams_from_csv/$', views.CompetitionOrganizerCSVTeams.as_view(), name='create_org_teams_from_csv'),
    url(r'^(?P<competition_pk>\d+)/edit_org_team/(?P<pk>\d+)$', views.CompetitionOrganizerTeams.as_view(), name='edit_org_team'),
    url(r'^(?P<competition_pk>\d+)/delete_org_team/(?P<team_pk>\d+)$', views.delete_organizer_team, name='delete_org_team'),
]
