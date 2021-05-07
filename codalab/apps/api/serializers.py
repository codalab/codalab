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
        fields = ('id','status','status_details','submitted_at','submission_number', 'file', 'filename', 'exception_details', 'description', 'method_name', 'method_description', 'project_url', 'publication_url', 'bibtex', 'organization_or_affiliation')
        read_only_fields = ('participant', 'phase', 'id','status_details','submitted_at','submission_number', 'exception_details')


class CompetitionSubmissionListSerializer(serializers.ModelSerializer):
    status = serializers.SlugField(source="status.codename", read_only=True)
    filename = serializers.Field(source="get_filename")
    username = serializers.CharField(source='participant.user.username')
    leaderboard = serializers.SerializerMethodField('get_leaderboard')
    can_be_migrated = serializers.SerializerMethodField('get_can_be_migrated')
    participant_submission_number = serializers.CharField(read_only=True)
    phase_number = serializers.IntegerField(source='phase.phasenumber')
    size = serializers.SerializerMethodField('get_size')

    class Meta:
        model = webmodels.CompetitionSubmission
        fields = (
            'id',
            'status',
            'submission_number',
            'participant_submission_number',
            'phase',
            'phase_number',
            'submitted_at',
            'leaderboard',
            # 'results',
            'filename',
            'username',
            'is_migrated',
            'size',

            # Is it possible to migrate this to the next phase?
            'can_be_migrated',
        )

    def get_leaderboard(self, instance):
        return instance.id in self.context['leaderboard_submissions']

    def get_can_be_migrated(self, instance):
        return instance.id in self.context['migratable_submissions']

    def get_size(self, instance):
        return instance.size


class PhaseSerial(serializers.ModelSerializer):
    start_date = serializers.DateField(format='%Y-%m-%d')

    class Meta:
        model = webmodels.CompetitionPhase
        read_only_fields = ['datasets']


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
