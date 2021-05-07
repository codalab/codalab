# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CompetitionPhase.max_submission_size'
        db.add_column(u'web_competitionphase', 'max_submission_size',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CompetitionPhase.participant_max_storage_use'
        db.add_column(u'web_competitionphase', 'participant_max_storage_use',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CompetitionPhase.max_submission_size'
        db.delete_column(u'web_competitionphase', 'max_submission_size')

        # Deleting field 'CompetitionPhase.participant_max_storage_use'
        db.delete_column(u'web_competitionphase', 'participant_max_storage_use')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'authenz.cluser': {
            'Meta': {'object_name': 'ClUser'},
            'allow_admin_status_updates': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'allow_forum_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bibtex': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chahub_data_hash': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chahub_needs_retry': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'chahub_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_on_submission_finished_successfully': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'method_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'method_name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'newsletter_opt_in': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organization_or_affiliation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'organizer_direct_message_updates': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'organizer_status_updates': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'participation_status_updates': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'project_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publication_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'rabbitmq_password': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'rabbitmq_queue_limit': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5', 'blank': 'True'}),
            'rabbitmq_username': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'team_members': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'team_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'queues.queue': {
            'Meta': {'object_name': 'Queue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'organizers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'organizers'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['authenz.ClUser']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['authenz.ClUser']"}),
            'vhost': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'teams.team': {
            'Meta': {'unique_together': "(('name', 'competition'),)", 'object_name': 'Team'},
            'allow_requests': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.Competition']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_creator'", 'to': u"orm['authenz.ClUser']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_url_base': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'to': u"orm['authenz.ClUser']", 'through': u"orm['teams.TeamMembership']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['teams.TeamStatus']", 'null': 'True'})
        },
        u'teams.teammembership': {
            'Meta': {'object_name': 'TeamMembership'},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_invitation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_request': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['teams.TeamMembershipStatus']", 'null': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_memberships'", 'to': u"orm['authenz.ClUser']"})
        },
        u'teams.teammembershipstatus': {
            'Meta': {'object_name': 'TeamMembershipStatus'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'teams.teamstatus': {
            'Meta': {'object_name': 'TeamStatus'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'web.competition': {
            'Meta': {'ordering': "['end_date']", 'object_name': 'Competition'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competition_admins'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['authenz.ClUser']"}),
            'allow_organizer_teams': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_public_submissions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_teams': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'anonymous_leaderboard': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'chahub_data_hash': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chahub_needs_retry': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'chahub_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'competition_docker_image': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitioninfo_creator'", 'to': u"orm['authenz.ClUser']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disallow_leaderboard_modifying': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_detailed_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_forum': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_medical_image_viewer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_per_submission_metadata': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enable_teams': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'force_submission_to_leaderboard': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_registration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hide_chart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hide_top_three': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_url_base': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_migrating': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_migrating_delayed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'last_phase_migration': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitioninfo_modified_by'", 'to': u"orm['authenz.ClUser']"}),
            'original_yaml_file': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'queue': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'competitions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['queues.Queue']"}),
            'require_team_approval': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'reward': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'secret_key': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'show_datasets_from_yaml': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'teams': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'competition_teams'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['teams.Team']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url_redirect': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'web.competitiondefbundle': {
            'Meta': {'object_name': 'CompetitionDefBundle'},
            'competition': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'bundle'", 'unique': 'True', 'null': 'True', 'to': u"orm['web.Competition']"}),
            'config_bundle': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owner'", 'to': u"orm['authenz.ClUser']"}),
            's3_config_bundle': ('s3direct.fields.S3DirectField', [], {'null': 'True', 'blank': 'True'})
        },
        u'web.competitiondump': {
            'Meta': {'object_name': 'CompetitionDump'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dumps'", 'to': u"orm['web.Competition']"}),
            'data_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Starting'", 'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'web.competitionparticipant': {
            'Meta': {'unique_together': "(('user', 'competition'),)", 'object_name': 'CompetitionParticipant'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participants'", 'to': u"orm['web.Competition']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.ParticipantStatus']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participation'", 'to': u"orm['authenz.ClUser']"})
        },
        u'web.competitionphase': {
            'Meta': {'ordering': "['phasenumber']", 'object_name': 'CompetitionPhase'},
            'auto_migration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '24', 'null': 'True', 'blank': 'True'}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phases'", 'to': u"orm['web.Competition']"}),
            'datasets': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'phase'", 'blank': 'True', 'to': u"orm['web.Dataset']"}),
            'default_docker_image': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'disable_custom_docker_image': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'execution_time_limit': ('django.db.models.fields.PositiveIntegerField', [], {'default': '300'}),
            'force_best_submission_to_leaderboard': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ingestion_program': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ingestion_program_docker_image': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'ingestion_program_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ingestion_program_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"}),
            'input_data': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'input_data_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'input_data_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"}),
            'is_migrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_scoring_only': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'leaderboard_management_mode': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '50'}),
            'max_submission_size': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'max_submissions': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'}),
            'max_submissions_per_day': ('django.db.models.fields.PositiveIntegerField', [], {'default': '999'}),
            'participant_max_storage_use': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'phase_never_ends': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phasenumber': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'public_data': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'public_data_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'public_data_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"}),
            'reference_data': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reference_data_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reference_data_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"}),
            'scoring_program': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'scoring_program_docker_image': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'scoring_program_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'scoring_program_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'starting_kit': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'starting_kit_organizer_dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'starting_kit_organizer_dataset'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['web.OrganizerDataSet']"})
        },
        u'web.competitionsubmission': {
            'Meta': {'unique_together': "(('submission_number', 'phase', 'participant'),)", 'object_name': 'CompetitionSubmission'},
            'bibtex': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chahub_data_hash': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'chahub_needs_retry': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'chahub_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'completed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'coopetition_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'detailed_results_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'dislike_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'docker_image': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'exception_details': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'execution_key': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'file_url_base': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'history_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ingestion_program_stderr_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ingestion_program_stdout_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'inputfile': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'is_migrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'like_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'method_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'method_name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'organization_or_affiliation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'output_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': u"orm['web.CompetitionParticipant']"}),
            'phase': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': u"orm['web.CompetitionPhase']"}),
            'prediction_output_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'prediction_runfile': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'prediction_stderr_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'prediction_stdout_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'private_output_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'project_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publication_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'queue_name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'readable_filename': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'runfile': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            's3_file': ('s3direct.fields.S3DirectField', [], {'null': 'True', 'blank': 'True'}),
            'scores_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.CompetitionSubmissionStatus']"}),
            'status_details': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'stderr_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'stdout_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sub_size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'submission_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'submitted_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'team'", 'null': 'True', 'to': u"orm['teams.Team']"}),
            'team_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'when_made_public': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'when_unmade_public': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'web.competitionsubmissionmetadata': {
            'Meta': {'object_name': 'CompetitionSubmissionMetadata'},
            'beginning_cpu_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'beginning_swap_memory_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'beginning_virtual_memory_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_cpu_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_swap_memory_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_virtual_memory_usage': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ingestion_program_duration': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_predict': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_scoring': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'processes_running_in_temp_dir': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadatas'", 'to': u"orm['web.CompetitionSubmission']"})
        },
        u'web.competitionsubmissionstatus': {
            'Meta': {'object_name': 'CompetitionSubmissionStatus'},
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'web.contentcategory': {
            'Meta': {'object_name': 'ContentCategory'},
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'content_limit': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_menu': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['web.ContentCategory']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'visibility': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.ContentVisibility']"})
        },
        u'web.contentvisibility': {
            'Meta': {'object_name': 'ContentVisibility'},
            'classname': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'web.dataset': {
            'Meta': {'ordering': "['number']", 'object_name': 'Dataset'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'datasets'", 'to': u"orm['authenz.ClUser']"}),
            'datafile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.ExternalFile']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'web.defaultcontentitem': {
            'Meta': {'object_name': 'DefaultContentItem'},
            'category': ('mptt.fields.TreeForeignKey', [], {'to': u"orm['web.ContentCategory']"}),
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_visibility': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.ContentVisibility']"}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'rank': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'web.externalfile': {
            'Meta': {'object_name': 'ExternalFile'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['authenz.ClUser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source_address_info': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.ExternalFileType']"})
        },
        u'web.externalfilesource': {
            'Meta': {'object_name': 'ExternalFileSource'},
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'service_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'web.externalfiletype': {
            'Meta': {'object_name': 'ExternalFileType'},
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'web.organizerdataset': {
            'Meta': {'object_name': 'OrganizerDataSet'},
            'data_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sub_data_files': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['web.OrganizerDataSet']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '64'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['authenz.ClUser']"})
        },
        u'web.page': {
            'Meta': {'ordering': "['category', 'rank']", 'unique_together': "(('label', 'category', 'container'),)", 'object_name': 'Page'},
            'category': ('mptt.fields.TreeForeignKey', [], {'to': u"orm['web.ContentCategory']"}),
            'codename': ('django.db.models.fields.SlugField', [], {'max_length': '100'}),
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'null': 'True', 'to': u"orm['web.Competition']"}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['web.PageContainer']"}),
            'defaults': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.DefaultContentItem']", 'null': 'True', 'blank': 'True'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'markup': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'visibility': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'web.pagecontainer': {
            'Meta': {'unique_together': "(('object_id', 'content_type'),)", 'object_name': 'PageContainer'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'web.participantstatus': {
            'Meta': {'object_name': 'ParticipantStatus'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'web.phaseleaderboard': {
            'Meta': {'object_name': 'PhaseLeaderBoard'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'board'", 'unique': 'True', 'to': u"orm['web.CompetitionPhase']"})
        },
        u'web.phaseleaderboardentry': {
            'Meta': {'unique_together': "(('board', 'result'),)", 'object_name': 'PhaseLeaderBoardEntry'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': u"orm['web.PhaseLeaderBoard']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'leaderboard_entry_result'", 'to': u"orm['web.CompetitionSubmission']"})
        },
        u'web.submissioncomputedscore': {
            'Meta': {'object_name': 'SubmissionComputedScore'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'scoredef': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'computed_score'", 'unique': 'True', 'to': u"orm['web.SubmissionScoreDef']"}),
            'weights': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'web.submissioncomputedscorefield': {
            'Meta': {'object_name': 'SubmissionComputedScoreField'},
            'computed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fields'", 'to': u"orm['web.SubmissionComputedScore']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scoredef': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionScoreDef']"})
        },
        u'web.submissionresultgroup': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'SubmissionResultGroup'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'phases': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['web.CompetitionPhase']", 'through': u"orm['web.SubmissionResultGroupPhase']", 'symmetrical': 'False'})
        },
        u'web.submissionresultgroupphase': {
            'Meta': {'unique_together': "(('group', 'phase'),)", 'object_name': 'SubmissionResultGroupPhase'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionResultGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.CompetitionPhase']"})
        },
        u'web.submissionscore': {
            'Meta': {'unique_together': "(('result', 'scoredef'),)", 'object_name': 'SubmissionScore'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scores'", 'to': u"orm['web.CompetitionSubmission']"}),
            'scoredef': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionScoreDef']"}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '10'})
        },
        u'web.submissionscoredef': {
            'Meta': {'unique_together': "(('key', 'competition'),)", 'object_name': 'SubmissionScoreDef'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.Competition']"}),
            'computed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['web.SubmissionResultGroup']", 'through': u"orm['web.SubmissionScoreDefGroup']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'numeric_format': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'selection_default': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'show_rank': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sorting': ('django.db.models.fields.SlugField', [], {'default': "'asc'", 'max_length': '20'})
        },
        u'web.submissionscoredefgroup': {
            'Meta': {'unique_together': "(('scoredef', 'group'),)", 'object_name': 'SubmissionScoreDefGroup'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionResultGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scoredef': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionScoreDef']"})
        },
        u'web.submissionscoreset': {
            'Meta': {'unique_together': "(('key', 'competition'),)", 'object_name': 'SubmissionScoreSet'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.Competition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['web.SubmissionScoreSet']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'scoredef': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['web.SubmissionScoreDef']", 'null': 'True', 'blank': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['web']