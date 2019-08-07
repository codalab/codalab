from rest_framework import serializers
from apps.web import models as webmodels
import django_filters

class ContentCategorySerial(serializers.ModelSerializer):
    visibility = serializers.SlugField(source='visibility.codename')

    class Meta:
        model = webmodels.ContentCategory

class DefaultContentSerial(serializers.ModelSerializer):
    category_codename = serializers.SlugField(source='category.codename')
    category_name = serializers.CharField(source='category.name')
    initial_visibility = serializers.SlugField(source='initial_visibility.codename')
    class Meta:
        model = webmodels.DefaultContentItem

class PageSerial(serializers.ModelSerializer):
    container = serializers.RelatedField(required=False)

    class Meta:
        model = webmodels.Page

    def validate_container(self,attr,source):
        ## The container, if not supplied will be supplied by the view
        ## based on url kwargs.
        if 'container' in self.context:
            attr['container'] = self.context['container']
        return attr

class CompetitionDatasetSerial(serializers.ModelSerializer):
    dataset_id = serializers.IntegerField()
    source_url = serializers.URLField()
    source_address_info = serializers.CharField()
    competition_id = serializers.IntegerField()
    phase_id = serializers.IntegerField()

    def validata_phase_id(self,attr,source):
        if not attr[source]:
            attr[source] = None
        return attr

class CompetitionParticipantSerial(serializers.ModelSerializer):
    class Meta:
        model = webmodels.CompetitionParticipant

class CompetitionSubmissionSerial(serializers.ModelSerializer):
    status = serializers.SlugField(source="status.codename", read_only=True)
    filename = serializers.Field(source="get_filename")
    class Meta:
        model = webmodels.CompetitionSubmission
        fields = ('id','status','status_details','submitted_at','submission_number', 'file', 'filename', 'exception_details', 'description')
        read_only_fields = ('participant', 'phase', 'id','status_details','submitted_at','submission_number', 'exception_details')

class PhaseSerial(serializers.ModelSerializer):
    start_date = serializers.DateField(format='%Y-%m-%d')
    is_active = serializers.Field()

    class Meta:
        model = webmodels.CompetitionPhase
        fields = (
            'competition',
            'description',
            'phasenumber',
            'label',
            'start_date',
            'max_submissions',
            'max_submissions_per_day',
            'is_scoring_only',
            'scoring_program',
            'reference_data',
            'input_data',
            'datasets',
            'leaderboard_management_mode',
            'force_best_submission_to_leaderboard',
            'auto_migration',
            'is_migrated',
            'is_active',
            'execution_time_limit',
            'color',
            'input_data_organizer_dataset',
            'reference_data_organizer_dataset',
            'scoring_program_organizer_dataset',
            'phase_never_ends',
            'scoring_program_docker_image',
            'default_docker_image',
            'disable_custom_docker_image',
            'starting_kit',
            'starting_kit_organizer_dataset',
            'public_data',
            'public_data_organizer_dataset',
            'ingestion_program',
            'ingestion_program_docker_image',
            'ingestion_program_organizer_dataset',
        )
        extra_kwargs = {
            'datasets': {'read_only': True},
            'is_active': {'read_only': True},
        }

class CompetitionPhaseSerial(serializers.ModelSerializer):
    end_date = serializers.DateField(format='%Y-%m-%d')
    phases = PhaseSerial(many=True)

    class Meta:
        model = webmodels.Competition
        fields = ['end_date','phases']

class LeaderBoardSerial(serializers.ModelSerializer):
    entries =  CompetitionSubmissionSerial(read_only=True, source='submissions')
    class Meta:
        model = webmodels.PhaseLeaderBoard

class CompetitionDataSerial(serializers.ModelSerializer):
    image_url = serializers.URLField(source='image.url', read_only=True)
    phases = serializers.RelatedField(many=True)
    class Meta:
        model = webmodels.Competition

class PhaseRel(serializers.RelatedField):

    # TODO: Some cleanup and validation to do
    def to_native(self,value):
        o = PhaseSerial(instance=value)
        return o.data

    def from_native(self,data=None,files=None):
        kw = {'data': data,'partial':self.partial}
        args = []
        print data
        print type(data)
        if 'id' in data:
            instance = webmodels.CompetitionPhase.objects.filter(pk=data['id']).get()
            args.append(instance)
            print instance
        o = PhaseSerial(*args,**kw)

        if o.is_valid():
            return o.object
        else:
            raise Exception(o.errors)

class CompetitionSerial(serializers.ModelSerializer):
    phases = PhaseRel(many=True,read_only=False)
    image_url = serializers.CharField(source='image_url',read_only=True)
    pages = PageSerial(source='pagecontent.pages', read_only=True)

    class Meta:
        model = webmodels.Competition
        read_only_fields = ['image_url_base']

class CompetitionFilter(django_filters.FilterSet):
    creator = django_filters.CharFilter(name="creator__username")
    class Meta:
        model = webmodels.Competition
        fields = ['creator']

class ScoreSerial(serializers.ModelSerializer):
    class Meta:
        model = webmodels.SubmissionScore

class CompetitionScoresSerial(serializers.ModelSerializer):
    competition_id = serializers.IntegerField(source='phase.competition.pk')
    phase_id = serializers.IntegerField(source='phase.pk')
    phasenumber = serializers.IntegerField(source='phase.pk')
    partitipant_id = serializers.IntegerField(source='participant.pk')
    status = serializers.CharField(source='status.codename')
    status_details = serializers.CharField(source='status_details')
    scores = ScoreSerial(read_only=True)

    class Meta:
        model = webmodels.CompetitionSubmission
