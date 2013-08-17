import json
from . import serializers
from rest_framework import (viewsets,views,permissions)
from rest_framework.decorators import action,link
from rest_framework.response import Response
from rest_framework import renderers
from apps.web import models as webmodels
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

class CompetitionAPIViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompetitionSerial
    queryset = webmodels.Competition.objects.all()

    def destroy(self, request, pk):
        """
        Cleanup the destruction of a competition.

        This requires removing phases, submissions, and participants. We should try to design 
        the models to make the cleanup simpler if we can.
        """
        # Get the competition
        c = Competition.objects.get(id=pk)

        # for each phase, cleanup the leaderboard and submissions
        print "You called destroy on %s!" % pk
        return Response(json.dumps(dict()), content_type="application/json")

    @action(permission_classes=[permissions.IsAuthenticated])
    def participate(self,request,pk=None):
        comp = self.get_object()
        terms = request.DATA['agreed_terms']
        status = webmodels.ParticipantStatus.objects.get(codename='pending')
        p,cr = webmodels.CompetitionParticipant.objects.get_or_create(user=self.request.user,
                                                                   competition=comp,
                                                                   defaults={'status': status,
                                                                             'reason': None})
        response_data = {
            'result' : 201 if cr else 200,
            'id' : p.id
        }

        return Response(json.dumps(response_data), content_type="application/json")
    
    def _get_userstatus(self,request,pk=None,participant_id=None):
        comp = self.get_object()
        resp = {}
        status = 200
        try:
            p = webmodels.CompetitionParticipant.objects.get(user=self.request.user,competition=comp)
            resp = {'status': p.status.codename, 'reason': p.reason}
        except ObjectDoesNotExist:
            resp = {'status': None, 'reason': None}
            status = 400
        return Response(resp,status=status)

    @link(permission_classes=[permissions.IsAuthenticated])
    def mystatus(self,request,pk=None):
        return self._get_userstatus(request,pk)

    @action(methods=['POST','PUT'], permission_classes=[permissions.IsAuthenticated])
    def participation_status(self,request,pk=None):
        print "made it into handler"
        comp = self.get_object()
        resp = {}
        status = request.DATA['status']
        part = request.DATA['participant_id']
        reason = request.DATA['reason']

        try:
            p = webmodels.CompetitionParticipant.objects.get(competition=comp, pk=part)
            p.status = webmodels.ParticipantStatus.objects.get(codename=status)
            p.reason = reason
            p.save()
            resp = { 
                'status': status,
                'participantId': part,
                'reason': reason 
                }
        except ObjectDoesNotExist as e:
            resp = {
                'status' : 400
                }      
        
        return Response(json.dumps(resp), content_type="application/json")
            
    @action(permission_classes=[permissions.IsAuthenticated])
    def info(self,request,*args,**kwargs):
        comp = self.get_object()
        comp.title = request.DATA.get('title')
        comp.description = request.DATA.get('description')
        comp.save()
        return Response({"data":{"title":comp.title,"description":comp.description,"imageUrl":comp.image.url if comp.image else None},"published":3},status=200)

competition_list =   CompetitionAPIViewSet.as_view({'get':'list','post':'create', 'post': 'participate',})
competition_retrieve =   CompetitionAPIViewSet.as_view({'get':'retrieve','put':'update', 'patch': 'partial_update'})

class CompetitionPhaseEditView(views.APIView):
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer)

    def post(self,request,*args,**kwargs):
        serial = serializers.CompetitionPhasesEditSerial(data=request.DATA)
        if not serial.is_valid():
            raise Exception(serial.errors)
        comp = webmodels.Competition.objects.get(pk=kwargs.get('competition_id'))
        if serial.data['end_date']:
            comp.end_date = serial.data['end_date']
            comp.save()
        for p in serial.data['phases']:
            if p['phase_id']:
                phase = webmodels.CompetitionPhase.objects.get(pk = p['phase_id'],competition=comp)
            else:
                phase = webmodels.CompetitionPhase.objects.create(competition=comp,label=p['label'],
                                                                  start_date=p['start_date'],
                                                                  phasenumber=p['phasenumber'],
                                                                  max_submissions=p['max_submissions'])
        return Response(status=200)

class CompetitionParticipantAPIViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompetitionParticipantSerial
    queryset = webmodels.CompetitionParticipant.objects.all()
    
    def get_queryset(self):
        competition_id = self.kwargs.get('competition_id',None)
        return self.queryset.filter(competition__pk=competition_id)

class CompetitionPhaseAPIViewset(viewsets.ModelViewSet):
    serializer_class = serializers.CompetitionPhaseSerial
    queryset = webmodels.Competition.objects.all()
    
    def get_queryset(self):
        competition_id = self.kwargs.get('pk',None)
        phasenumber = self.kwargs.get('phasenumber',None)
        kw = {}
        if competition_id:
            kw['pk'] = competition_id
        if phasenumber:
            kw['phases__phasenumber'] = phasenumber
        return self.queryset.filter(**kw)

competitionphase_list = CompetitionPhaseAPIViewset.as_view({'get':'list','post':'create'})
competitionphase_retrieve = CompetitionPhaseAPIViewset.as_view({'get':'retrieve','put':'update','patch':'partial_update'})


class CompetitionPageViewSet(viewsets.ModelViewSet):
    ## TODO: Turn the custom logic here into a mixin for other content
    serializer_class = serializers.PageSerial  
    content_type = ContentType.objects.get_for_model(webmodels.Competition)
    queryset = webmodels.Page.objects.all()
    _pagecontainer = None
    _pagecontainer_q = None

    def get_queryset(self):
        kw = {}
        if 'competition_id' in self.kwargs:
            kw['container__object_id'] = self.kwargs['competition_id']
            kw['container__content_type'] = self.content_type
        if 'category' in self.kwargs:
            kw['category__codename'] = self.kwargs['category']
        if kw:
            return self.queryset.filter(**kw)
        else:
            return self.queryset

    def dispatch(self,request,*args,**kwargs):        
        if 'competition_id' in kwargs:
            self._pagecontainer_q = webmodels.PageContainer.objects.filter(object_id=kwargs['competition_id'],
                                                                           content_type=self.content_type)
        return super(CompetitionPageViewSet,self).dispatch(request,*args,**kwargs)

    @property
    def pagecontainer(self):
        if self._pagecontainer_q is not None and self._pagecontainer is None: 
            try:
                self._pagecontainer = self._pagecontainer_q.get()
            except ObjectDoesNotExist:
                self._pagecontainer = None
        return self._pagecontainer
    
    def new_pagecontainer(self,competition_id):
        try:
            competition=webmodels.Competition.objects.get(pk=competition_id)
        except ObjectDoesNotExist:
            raise Http404
        self._pagecontainer = webmodels.PageContainer.objects.create(object_id=competition_id,
                                                                     content_type=self.content_type)
        return self._pagecontainer

    def get_serializer_context(self):
        ctx = super(CompetitionPageViewSet,self).get_serializer_context()
        if 'competition_id' in self.kwargs:
            ctx.update({'container': self.pagecontainer})
        return ctx

    def create(self,request,*args,**kwargs):        
        container = self.pagecontainer
        if not container:
            container = self.new_pagecontainer(self.kwargs.get('competition_id'))           
        return  super(CompetitionPageViewSet,self).create(request,*args,**kwargs)

competition_page_list = CompetitionPageViewSet.as_view({'get':'list','post':'create'})
competition_page = CompetitionPageViewSet.as_view({'get':'retrieve','put':'update','patch':'partial_update'})

class CompetitionSubmissionResultViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SubmissionResultSerial
    queryset = webmodels.SubmissionResult.objects.all()
    _file = None

    @action(permission_classes=[permissions.IsAuthenticated], methods=["DELETE"])
    def leaderboard_remove(self, request, pk=None, competition_id=None, submission_id=None):
        submission = webmodels.CompetitionSubmission.objects.get(id=submission_id)
        result = self.get_object()
        response = dict()
        if submission.phase.is_active:
            lb = webmodels.PhaseLeaderBoard.objects.get(phase=submission.phase)
            lbe = webmodels.PhaseLeaderBoardEntry.objects.get(board=lb, submission=submission, result=result)
            lbe.delete()
            response['status'] = lbe.id
        else:
            response['status'] = 400
        
        return Response(response, status=response['status'], content_type="application/json")

    @action(permission_classes=[permissions.IsAuthenticated])
    def leaderboard(self, request, pk=None, competition_id=None, submission_id=None):
        submission = webmodels.CompetitionSubmission.objects.get(id=submission_id)
        result = self.get_object()
        response = dict()
        if submission.phase.is_active:
            lb,_ = webmodels.PhaseLeaderBoard.objects.get_or_create(phase=submission.phase)
            lbe,cr = webmodels.PhaseLeaderBoardEntry.objects.get_or_create(board=lb, submission=submission, result=result)
            response['status'] = (201 if cr else 200)
        else:
            response['status'] = 400
        return Response(response, status=response['status'], content_type="application/json")

class CompetitionSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CompetitionSubmissionSerial
    queryset = webmodels.CompetitionSubmission.objects.all()
    _file = None

    def get_queryset(self):
        return self.queryset.filter(phase__competition__pk=self.kwargs['competition_id'])

    def pre_save(self,obj):
        if obj.status_id is None:
            obj.status = webmodels.CompetitionSubmissionStatus.objects.get(codename='submitted')
        if obj.participant_id is None:
            obj.participant = self.request.user
        
class LeaderBoardViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.LeaderBoardSerial
    queryset = webmodels.PhaseLeaderBoard.objects.all()

    def get_queryset(self):
        kw = {}
        competition_id = self.kwargs.get('competition_id',None)
        phase_id = self.kwargs.get('phase_id',None)
        if phase_id:
            kw['phase__pk'] = phase_id
        if competition_id:
            kw['phase__competition__pk'] = competition_id
        return self.queryset.filter(**kw)

leaderboard_list = LeaderBoardViewSet.as_view({'get':'list','post':'create'} )
leaderboard_retrieve = LeaderBoardViewSet.as_view( {'get':'retrieve','put':'update','patch':'partial_update'} )

class DefaultContentViewSet(viewsets.ModelViewSet):
    queryset = webmodels.DefaultContentItem.objects.all()
    serializer_class = serializers.DefaultContentSerial
    
