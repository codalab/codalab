from django.db import models


class HealthSettings(models.Model):
    """Base Health Settings Model. Counts the amount of jobs ready to process."""
    emails = models.TextField(null=True, blank=True)
    threshold = models.PositiveIntegerField(default=25, null=True, blank=True)
    congestion_threshold = models.PositiveIntegerField(default=100, null=True, blank=True)


class StorageDataPoint(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    bucket_name = models.CharField(max_length=255)
    # As reported by the actual bucket contents
    total_use = models.BigIntegerField(default=0)
    # Submissions, datsets, dumps, bundles etc being used by the competition
    competition_use = models.BigIntegerField(default=0)
    # Use exclusively from submissions (All files, not just the uploaded zip)
    submission_use = models.BigIntegerField(default=0)
    # Use exclusively from datasets
    dataset_use = models.BigIntegerField(default=0)
    # Use exclusively from Bundles
    bundle_use = models.BigIntegerField(default=0)
    # Use exclusively from dumps
    dumps_use = models.BigIntegerField(default=0)
