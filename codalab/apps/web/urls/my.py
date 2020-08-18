from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required

from apps.web import views

partials_patterns = [
    url(r'^_competitions_managed$',
        login_required(views.MyCompetitionsManagedPartial.as_view()),
        name='my_competitions_managed'),
    url(r'^_competitions_entered$',
        login_required(views.MyCompetitionsEnteredPartial.as_view()),
        name='my_competitions_entered'),
    url(r'^(?P<phase_id>\d+)/(?P<participant_id>\d+)/_submission_results',
        login_required(views.MySubmissionResultsPartial.as_view()),
        name='my_competition_submissions'),
]

urlpatterns = [
    url(r'^$', views.my_index, name='competitions'),
    url(r'^competition/(?P<competition_id>\d+)/participants/',
        views.MyCompetitionParticipantView.as_view(),
        name='my_competition_participants'),
    url(r'^competition/(?P<competition_id>\d+)/submissions/',
        views.MyCompetitionSubmissionsPage.as_view(),
        name='my_competition_submissions'),
    url(r'^competition/submission/(?P<submission_id>\d+)/(?P<filetype>stdout.txt|stderr.txt|input.zip|prediction-output.zip|output.zip|private_output.zip|detailed_results.html|predict_stdout.txt|predict_stderr.txt|ingestion_program_stdout_file.txt|ingestion_program_stderr_file.txt)$',
        views.MyCompetitionSubmissionOutput.as_view(),
        name='my_competition_output'),
    url(r'^competition/submission/(?P<submission_id>\d+)/toggle_make_public',
        views.MyCompetitionSubmissionToggleMakePublic.as_view(),
        name='my_competition_toggle_make_public'),
    url(r'^competition/submission/(?P<submission_id>\d+)/detailed_results/',
        views.MyCompetitionSubmissionDetailedResults.as_view(),
        name='my_competition_detailed_results'),
    url(r'^_partials/', include(partials_patterns)),
    url(r'^datasets/$', views.OrganizerDataSetListView.as_view(), name='my_datasets'),
    url(r'^datasets/create', views.OrganizerDataSetCreate.as_view(), name='my_datasets_create'),
    url(r'^datasets/update/(?P<pk>\d+)', views.OrganizerDataSetUpdate.as_view(), name='my_datasets_update'),
    url(r'^datasets/delete/(?P<pk>\d+)', views.OrganizerDataSetDelete.as_view(), name='my_datasets_delete'),
    url(r'^datasets/delete_multiple/', views.datasets_delete_multiple, name="datasets_delete_multiple"),
    url(r'^datasets/download/(?P<dataset_key>.+)', views.download_dataset, name='datasets_download'),

    # User settings
    url(r'^settings/', views.UserSettingsView.as_view(), name='user_settings')
]
