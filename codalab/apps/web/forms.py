import os

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q
from s3direct.widgets import S3DirectWidget

import models
from tinymce.widgets import TinyMCE

from apps.queues.models import Queue
from apps.web.models import PageContainer
from apps.web.models import ContentCategory
from apps.web.models import SubmissionScoreSet
from apps.web.utils import clean_html_script
from apps.web.tasks import _make_url_sassy

from apps.authenz.models import ClUser

User = get_user_model()


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = models.Competition
        fields = (
            'title',
            'description',
            'queue',
            'disallow_leaderboard_modifying',
            'force_submission_to_leaderboard',
            'image',
            'end_date',
            'published',
            'enable_medical_image_viewer',
            'enable_detailed_results',
            'admins',
            'show_datasets_from_yaml',
            'reward',
            'allow_teams',
            'enable_per_submission_metadata',
            'allow_public_submissions',
            'enable_forum',
            'anonymous_leaderboard',
            'enable_teams',
            'allow_organizer_teams',
            'require_team_approval',
            'competition_docker_image',
            'hide_top_three',
            'hide_chart',
            'has_registration',
            'url_redirect',
        )
        widgets = {'description': TinyMCE(attrs={'rows' : 20, 'class' : 'competition-editor-description'},
                                          mce_attrs={"theme": "advanced", "cleanup_on_startup": True, "theme_advanced_toolbar_location": "top", "gecko_spellcheck": True})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(CompetitionForm, self).__init__(*args, **kwargs)

        # Get public queues and include current queue instance if it's selected
        filters = Q(is_public=True) | Q(owner=user) | Q(organizers__in=[user])
        if self.instance.queue:
            filters |= Q(pk=self.instance.queue.pk)

        self.fields["queue"].choices = [("", "Default")]
        self.fields["queue"].choices += Queue.objects.filter(filters).values_list('pk', 'name').distinct()


class CompetitionPhaseForm(forms.ModelForm):
    class Meta:
        model = models.CompetitionPhase
        fields = (
            'phasenumber',
            'description',
            'label',
            'start_date',
            'max_submissions',
            'max_submissions_per_day',
            'execution_time_limit',
            'max_submission_size',
            'participant_max_storage_use',
            'color',
            'is_scoring_only',
            'auto_migration',
            'leaderboard_management_mode',
            'starting_kit_organizer_dataset',
            'public_data_organizer_dataset',
            'input_data_organizer_dataset',
            'reference_data_organizer_dataset',
            'scoring_program_organizer_dataset',
            'phase_never_ends',
            'force_best_submission_to_leaderboard',
            'delete_submissions_except_best_and_last',
            'ingestion_program_organizer_dataset',
            # 'default_docker_image`,
            # 'disable_custom_docker_image',
            # 'scoring_program_docker_image',
            # 'ingestion_program_docker_image',
        )
        # labels = {
        #     'default_docker_image': "Default participant docker image",
        # }
        widgets = {
            'leaderboard_management_mode' : forms.Select(
                attrs={'class': 'competition-editor-phase-leaderboard-mode'},
                choices=(('default', 'Default'), ('hide_results', 'Hide Results'))
            ),
            'DELETE' : forms.HiddenInput,
            # 'phasenumber': forms.HiddenInput
        }

    def clean_reference_data_organizer_dataset(self):
        # If no reference_data
        if not self.instance.reference_data and not self.cleaned_data["reference_data_organizer_dataset"]:
            raise forms.ValidationError("Phase has no reference_data set or chosen in the form, but it is required")

        # If we were using org dataset but do not select a new one
        if self.instance.reference_data_organizer_dataset and not self.cleaned_data["reference_data_organizer_dataset"]:
            raise forms.ValidationError("Phase has no reference_data set or chosen in the form, but it is required")

        return self.cleaned_data["reference_data_organizer_dataset"]

    def clean_scoring_program_organizer_dataset(self):
        # If no scoring_data
        if not self.instance.scoring_program and not self.cleaned_data["scoring_program_organizer_dataset"]:
            raise forms.ValidationError("Phase has no scoring_program set or chosen in the form, but it is required")

        # If we were using org dataset but do not select a new one
        if self.instance.scoring_program_organizer_dataset and not self.cleaned_data["scoring_program_organizer_dataset"]:
            raise forms.ValidationError("Phase has no scoring_program set or chosen in the form, but it is required")

        return self.cleaned_data["scoring_program_organizer_dataset"]


class PageForm(forms.ModelForm):
    class Meta:
        model = models.Page
        fields = ('category', 'rank', 'label', 'html')
        widgets = { 'html' : TinyMCE(attrs={'rows' : 20, 'class' : 'competition-editor-page-html'},
                                     mce_attrs={"theme" : "advanced", "cleanup_on_startup" : True, "theme_advanced_toolbar_location" : "top", "gecko_spellcheck" : True}),
                    'DELETE' : forms.HiddenInput, 'container' : forms.HiddenInput}

    def clean_label(self):
        cleaned_data = super(PageForm, self).clean()
        label = cleaned_data.get('label')
        if label:
            existing_website = models.Page.objects.filter(
                competition=self.instance.competition,
                label=label
            ).exclude(pk=self.instance.pk)
            if existing_website.exists():
                raise forms.ValidationError('Website Name is invalid. This name is already in use.', code='invalid')
        return label

    def save(self, commit=True):

        instance = super(PageForm, self).save(commit=False)

        if instance.html:
            instance.html = clean_html_script(instance.html)

        if instance.pk is None:
            instance.codename = self.cleaned_data['label']
            page_container,_ = PageContainer.objects.get_or_create(object_id=instance.competition.id, content_type=ContentType.objects.get_for_model(instance.competition))
            details_category = ContentCategory.objects.get(name="Learn the Details")
            instance.category = details_category
            instance.container = page_container

        if commit:
            instance.save()

        return instance


class LeaderboardForm(forms.ModelForm):
    class Meta:
        model = models.SubmissionScoreDef
        fields = (
            'key',
            'label',
            'ordering',
            'numeric_format',
            'show_rank',
            'selection_default',
            'sorting',
        )

    # TODO, refactor save method
    # def save(self, commit=True):
    #     '''
    #     Save method override
    #     #TODO, look into refactoring to avoid overriding
    #     '''
    #     instance = super(LeaderboardForm, self).save(commit=False)

    #     submission_score_set = SubmissionScoreSet.objects.get(competition=instance.competition, key=instance.key)
    #     submission_score_set.label = instance.label
    #     submission_score_set.save()

    #     if commit:
    #         instance.save()

    #     return instance


class CompetitionDatasetForm(forms.ModelForm):
    class Meta:
        model = models.Dataset


class CompetitionParticipantForm(forms.ModelForm):
    class Meta:
        model = models.CompetitionParticipant


class OrganizerDataSetModelForm(forms.ModelForm):
    class Meta:
        model = models.OrganizerDataSet
        fields = ["name", "description", "type", "data_file", "sub_data_files"]

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user')
        super(OrganizerDataSetModelForm, self).__init__(*args, **kwargs)
        self.fields["sub_data_files"].widget.attrs["style"] = "width: 100%;"

        # If we have sub_data_files, then hide what is currently in data_file (which would be metadata containing references
        # to all of the sub_data_files)
        if self.instance.pk != None and self.instance.sub_data_files.count() > 0:
            self.fields["data_file"] = forms.FileField(initial=None, required=False)

    def clean_data_file(self):
        data = self.cleaned_data.get('data_file')

        # if data and self.data.get("sub_data_files"):
        #    raise forms.ValidationError("Cannot submit both single data file and multiple sub files!")
        # elif not data and not self.data.get("sub_data_files"):
        if not data and not self.data.get("sub_data_files"):
            raise forms.ValidationError("This field is required.")

        return data

    def save(self, commit=True):
        instance = super(OrganizerDataSetModelForm, self).save(commit=False)
        instance.uploaded_by = self.request_user

        if len(self.cleaned_data.get("sub_data_files")) > 0:
            instance.write_multidataset_metadata(datasets=self.cleaned_data.get("sub_data_files"))

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class UserSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = (
            'participation_status_updates',
            'organizer_status_updates',
            'organizer_direct_message_updates',
            'allow_admin_status_updates',
            'organization_or_affiliation',
            'allow_forum_notifications',
            'email_on_submission_finished_successfully',
            'newsletter_opt_in',
            'team_name',
            'team_members',
            'method_name',
            'method_description',
            'contact_email',
            'project_url',
            'publication_url',
            'bibtex',
            'first_name',
            'last_name',
            'email'
        )
        widgets = {
            'team_members': forms.Textarea(attrs={"class": "form-control"}),
            'method_description': forms.Textarea(attrs={"class": "form-control"}),
            'bibtex': forms.Textarea(attrs={"class": "form-control"})
        }


class CompetitionS3UploadForm(forms.ModelForm):

    class Meta:
        model = models.CompetitionDefBundle
        fields = ('s3_config_bundle',)

    def __init__(self, *args, **kwargs):
        # Call constructor before fields are built
        super(CompetitionS3UploadForm, self).__init__(*args, **kwargs)

        self.fields['s3_config_bundle'].required = True


class SubmissionS3UploadForm(forms.ModelForm):

    class Meta:
        model = models.CompetitionSubmission
        fields = ('s3_file',)

    def __init__(self, *args, **kwargs):
        # Call constructor before fields are built
        super(SubmissionS3UploadForm, self).__init__(*args, **kwargs)

        self.fields['s3_file'].required = True
        self.fields['s3_file'].label = ''
