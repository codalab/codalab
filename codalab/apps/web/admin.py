from django.contrib import admin
from . import models


class DatasetAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Dataset, DatasetAdmin)

class PhaseInlineAdmin(admin.TabularInline):
    model = models.CompetitionPhase


class ParticipantInlineAdmin(admin.TabularInline):
    model = models.CompetitionParticipant

class CompetitionAdmin(admin.ModelAdmin):
    inlines = [
               PhaseInlineAdmin,
               ParticipantInlineAdmin
               ]
admin.site.register(models.Competition, CompetitionAdmin)


class ParticipantAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.CompetitionParticipant, ParticipantAdmin)

class CompetitionPhaseAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.CompetitionPhase, CompetitionPhaseAdmin)

class ParticipantStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ParticipantStatus, ParticipantStatusAdmin)


class SubmissionStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.CompetitionSubmissionStatus, SubmissionStatusAdmin)

class ExternalFileAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ExternalFile, ExternalFileAdmin)

class ExternalFileTypeAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ExternalFileType, ExternalFileTypeAdmin)

class ExternalFileSourceAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ExternalFileSource, ExternalFileSourceAdmin)


class ContentCategoryAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ContentCategory, ContentCategoryAdmin)

class DefaultContentItemAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.DefaultContentItem, DefaultContentItemAdmin)


class PageGenAdmin(admin.StackedInline):
    model = models.Page

class ContentVisibilityAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ContentVisibility, ContentVisibilityAdmin)

class PageContainerAdmin(admin.ModelAdmin):
    inlines = [
        PageGenAdmin,
        ]
admin.site.register(models.PageContainer, PageContainerAdmin)

class PageAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Page, PageAdmin)

admin.site.register(models.OrganizerDataSet)
admin.site.register(models.CompetitionSubmission)
admin.site.register(models.CompetitionSubmissionMetadata)
admin.site.register(models.CompetitionDefBundle)
