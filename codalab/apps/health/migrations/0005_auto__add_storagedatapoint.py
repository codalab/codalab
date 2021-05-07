# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StorageDataPoint'
        db.create_table(u'health_storagedatapoint', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('bucket_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('total_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('competition_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('submission_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('dataset_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('bundle_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
            ('dumps_use', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
        ))
        db.send_create_signal(u'health', ['StorageDataPoint'])


    def backwards(self, orm):
        # Deleting model 'StorageDataPoint'
        db.delete_table(u'health_storagedatapoint')


    models = {
        u'health.healthsettings': {
            'Meta': {'object_name': 'HealthSettings'},
            'congestion_threshold': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100', 'null': 'True', 'blank': 'True'}),
            'emails': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'threshold': ('django.db.models.fields.PositiveIntegerField', [], {'default': '25', 'null': 'True', 'blank': 'True'})
        },
        u'health.storagedatapoint': {
            'Meta': {'object_name': 'StorageDataPoint'},
            'bucket_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'bundle_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'competition_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dataset_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'dumps_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'total_use': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['health']