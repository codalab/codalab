import logging
from apps.teams import forms
from apps.teams.forms import OrganizerTeamForm, OrganizerTeamsCSVForm
from apps.web.models import Competition, ParticipantStatus, CompetitionSubmission, get_current_phase
from apps.web.views import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, QueryDict, HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import TemplateView, FormView, UpdateView, CreateView

from .models import Team, TeamStatus, TeamMembership, TeamMembershipStatus, get_user_requests, get_competition_teams, \
    get_user_team, get_allowed_teams, get_team_pending_membership, get_competition_user_pending_teams, \
    get_team_submissions_inf

User = get_user_model()

logger = logging.getLogger(__name__)


class TeamDetailView(LoginRequiredMixin, TemplateView):
    # Serves the table of submissions in the Participate tab of a competition.
    # Requires an authenticated user who is an approved participant of the competition.
    template_name = 'teams/team_info.html'
    form_class = forms.TeamMembershipForm

    def post(self, request, *args, **kwargs):
        data = QueryDict(request.body)
        form_status = data['status']
        form_req_id = data['request_id']
        form_reason = data['reason']

        membership = TeamMembership.objects.get(pk=form_req_id)

        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        if competition.participants.filter(user__in=[membership.user]).exists():
            participant = competition.participants.get(user=membership.user)
            if participant.status.codename == ParticipantStatus.APPROVED:
                if get_user_team(participant, competition) is None:
                    membership.status = TeamMembershipStatus.objects.get(codename=form_status)
                    membership.reason = form_reason
                    if membership.status.codename == TeamMembershipStatus.REJECTED:
                        membership.end_date = now()
                    if membership.status.codename == TeamMembershipStatus.CANCELED:
                        membership.end_date = now()
                    membership.save()

                    # Close other requests
                    if membership.status.codename == TeamMembershipStatus.APPROVED:
                        current_requests = TeamMembership.objects.filter(
                            user=participant.user
                        ).all()
                        for req in current_requests:
                            if req.is_active and req.is_request and req != membership:
                                req.status = TeamMembershipStatus.objects.get(codename=TeamMembershipStatus.CANCELED)
                                req.end_date = now()
                                req.save()

        context = self.get_context_data()

        return super(TeamDetailView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context['team'] = None
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        context['competition'] = competition

        members_columns = [
            {
                'label': '#',
                'name': 'number'
            },
            {
                'label': 'NAME',
                'name': 'name'
            },
            {
                'label': 'EMAIL',
                'name': 'email'
            },
            {
                'label': 'JOINED',
                'name' : 'joined'
            },
            {
                'label': 'STATUS',
                'name': 'status'
            },
            {
                'label': 'ENTRIES',
                'name': 'entries'
            }
        ]

        try:
            participant = competition.participants.get(user=self.request.user)
            if participant.status.codename == ParticipantStatus.APPROVED:
                user_team = get_user_team(participant, competition)
                team_list = get_competition_teams(competition)
                user_requests = get_user_requests(participant, competition)
                user_pending_teams = get_competition_user_pending_teams(competition, participant)
                if user_team is not None:
                    context['team'] = user_team
                    context['team_requests'] = get_team_pending_membership(user_team)
                    owner_part=competition.participants.get(user=user_team.creator)
                    member_list=[
                        {
                            'pk': user_team.creator.pk,
                            'name': user_team.creator.username,
                            'email': user_team.creator.email,
                            'joined': user_team.created_at,
                            'status': 'creator',
                            'number':  1,
                            'entries': len(CompetitionSubmission.objects.filter(team=user_team, participant=owner_part)),
                        }
                    ]
                    status_approved = TeamMembershipStatus.objects.get(codename=TeamMembershipStatus.APPROVED)
                    for number, member in enumerate(user_team.members.all()):
                        member_part=competition.participants.get(user=member)
                        membership_set = member.team_memberships.filter(status=status_approved)
                        for membership in membership_set:
                            if membership is not None:
                                user_entry = {
                                    'pk': member.pk,
                                    'name': member.username,
                                    'email': member.email,
                                    'joined': membership.start_date,
                                    'status': membership.status.codename,
                                    'number': number + 2,
                                    'entries': len(CompetitionSubmission.objects.filter(team=user_team, participant=member_part)),
                                }
                                if user_entry['status'] == TeamMembershipStatus.APPROVED and membership.is_active:
                                    member_list.append(user_entry)
                    context['team_members']=member_list
                    context['members_columns'] = members_columns
                    context['active_phase'] = get_current_phase(competition)
                    context['submission_info_list'] = get_team_submissions_inf(user_team, context['active_phase'])
                context['requests'] = user_requests
                context['teams'] = team_list
                context['allowed_teams'] = get_allowed_teams(participant, competition)
                context['pending_teams'] = user_pending_teams

        except ObjectDoesNotExist:
            print("Participant not found")
            return Http404()

        return context


class RequestTeamView(TeamDetailView):

    def get_context_data(self, **kwargs):
        error = None
        action = self.kwargs['action']
        request = TeamMembership.objects.get(pk=self.kwargs['request_pk'])
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        if competition.participants.filter(user__in=[self.request.user]).exists():
            participant = competition.participants.get(user=self.request.user)
            if participant.status.codename == ParticipantStatus.APPROVED:
                if request.is_active:
                    if request.user==participant.user:
                        if action == 'accept':
                            if not request.is_invitation:
                                error="Invalid request type: Cannot accept your own request"
                            else:
                                request.is_accepted=True
                                request.status = TeamMembershipStatus.objects.get(
                                                        codename=TeamMembershipStatus.APPROVED)
                                request.save()
                        elif action == 'reject':
                            if not request.is_invitation:
                                error="Invalid request type: Cannot reject your own request"
                            else:
                                request.end_date=now()
                                request.status = TeamMembershipStatus.objects.get(
                                    codename=TeamMembershipStatus.REJECTED)
                                request.save()
                        elif action == 'cancel':
                            if not request.is_request:
                                error="Invalid request type: Cannot cancel an invitation"
                            else:
                                request.end_date=now()
                                request.status = TeamMembershipStatus.objects.get(
                                    codename=TeamMembershipStatus.CANCELED)
                                request.save()
                    elif request.team.creator==participant.user:
                        if action == 'accept':
                            if request.is_invitation:
                                error="Invalid request type: Cannot accept your own invitation"
                            else:
                                request.is_accepted=True
                                request.status = TeamMembershipStatus.objects.get(
                                    codename=TeamMembershipStatus.APPROVED)
                                request.save()
                        elif action == 'reject':
                            if request.is_invitation:
                                error="Invalid request type: Cannot reject your own invitation"
                            else:
                                request.end_date=now()
                                request.status = TeamMembershipStatus.objects.get(
                                    codename=TeamMembershipStatus.REJECTED)
                                request.save()
                        elif action == 'cancel':
                            if request.is_request:
                                error="Invalid request type: Cannot cancel a request"
                            else:
                                request.end_date=now()
                                request.status = TeamMembershipStatus.objects.get(
                                    codename=TeamMembershipStatus.CANCELED)
                                request.save()
                    else:
                        error = "You cannot modify this request"
                else:
                    error = "Invalid request: This request is not active"
                context=super(RequestTeamView, self).get_context_data(**kwargs)
                context['action']=action

                if error is not None:
                    context['error'] = error

        return context


class NewRequestTeamView(LoginRequiredMixin, CreateView):
    model = TeamMembership
    template_name = "teams/request.html"
    form_class = forms.TeamMembershipForm

    def get_success_url(self):
        competition = Competition.objects.get(pk=self.kwargs['competition_pk']);
        return reverse('team_detail', kwargs={'competition_pk': competition.pk})

    def get_context_data(self, **kwargs):
        context = super(NewRequestTeamView, self).get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(pk=self.kwargs['competition_pk'])
        context['team'] = Team.objects.get(pk=self.kwargs['team_pk'])
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.team = Team.objects.get(pk=self.kwargs['team_pk'])
        form.instance.start_date = now()
        form.instance.is_request = True
        form.instance.status = TeamMembershipStatus.objects.get(codename=TeamMembershipStatus.PENDING)
        form.save()
        return super(NewRequestTeamView, self).form_valid(form)


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    template_name = "teams/edit.html"
    form_class = forms.TeamEditForm

    def get_success_url(self):
        return reverse('team_detail', kwargs={'competition_pk': self.object.competition.pk})

    def get_context_data(self, **kwargs):
        context = super(TeamCreateView, self).get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(pk=self.kwargs['competition_pk'])
        return context

    def form_valid(self, form):
        form.instance.creator=self.request.user
        form.instance.created_at=now()
        form.instance.competition=Competition.objects.get(pk=self.kwargs['competition_pk'])
        if form.instance.competition.require_team_approval:
            form.instance.status = TeamStatus.objects.get(codename=TeamStatus.PENDING)
        else:
            form.instance.status = TeamStatus.objects.get(codename=TeamStatus.APPROVED)

        form.save()
        return super(TeamCreateView, self).form_valid(form)


class TeamEditView(LoginRequiredMixin, UpdateView):
    model = Team
    template_name = "teams/edit.html"
    form_class = forms.TeamEditForm
    pk_url_kwarg = 'team_pk'

    def get_success_url(self):
        return reverse('team_detail', kwargs={'competition_pk': self.object.competition.pk})

    def get_context_data(self, **kwargs):
        context = super(TeamEditView, self).get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(pk=self.kwargs['competition_pk'])
        context['information'] = {
            'Team name': self.object.name,
            'Description' : self.object.description,
            'Allow Requests': self.object.allow_requests,
            'Image': self.object.image
        }

        return context


class TeamCancelView(TeamDetailView):

    def get_context_data(self, **kwargs):
        error = None
        team = Team.objects.get(pk=self.kwargs['team_pk'])
        if team.creator == self.request.user:
            if team.status.codename == 'pending':
                status = TeamStatus.objects.get(codename="deleted")
                team.status = status
                team.save()
            else:
                error = "Invalid request: Only pending teams can be cancelled"
        else:
            error = "Invalid request: Only owner can cancel the team"

        context=super(TeamCancelView, self).get_context_data(**kwargs)
        if error is not None:
            context['error'] = error
        context['team'] = team
        return context


class CompetitionOrganizerTeams(FormView):
    form_class = OrganizerTeamForm
    template_name = 'teams/competitions/organizer_teams.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        if self.request.user != competition.creator:
            if self.request.user not in competition.admins.all():
                return HttpResponseForbidden(status=403)
        return super(CompetitionOrganizerTeams, self).dispatch(*args, **kwargs)

    def get_form(self, form_class=None):
        if not form_class:
            form_class = self.form_class
        if self.kwargs.get('pk'):
            current_team = Team.objects.get(pk=self.kwargs['pk'])
            return form_class(instance=current_team, **self.get_form_kwargs())
        else:
            return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(CompetitionOrganizerTeams, self).get_form_kwargs()
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        kwargs['competition_pk'] = self.kwargs['competition_pk']
        kwargs['creator_pk'] = competition.creator.pk
        return kwargs

    def form_valid(self, form):
        try:
            competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        except ObjectDoesNotExist:
            print("Could not find a competition for that PK!")
        form.save()
        self.success_url = reverse("my_competition_participants", kwargs={'competition_id': competition.pk})
        return super(CompetitionOrganizerTeams, self).form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=400)

    def get_context_data(self, **kwargs):
        context = super(CompetitionOrganizerTeams, self).get_context_data(**kwargs)
        try:
            if self.kwargs.get('pk'):
                team = Team.objects.get(pk=self.kwargs.get('pk'))
                context['initial_team_members'] = ','.join(list(team.members.all().values_list('username', flat=True)))
        except ObjectDoesNotExist:
            print("Could not find a team for that PK!")
        return context


@login_required
def delete_organizer_team(request, team_pk, competition_pk):

    if request.method == 'POST':
        try:
            comp = Competition.objects.get(pk=competition_pk)
            team_to_delete = Team.objects.get(pk=team_pk)

            if request.user != comp.creator:
                if request.user not in comp.admins.all():
                    return HttpResponseForbidden(status=403)

            logger.info("Deleting team {0} from competition {1}".format(team_to_delete, comp))
            team_to_delete.delete()
            return redirect('my_competition_participants', competition_id=comp.pk)
        except ObjectDoesNotExist:
            return HttpResponse(status=404)
    else:
        return HttpResponse(status=405)


class CompetitionOrganizerCSVTeams(FormView):
    form_class = OrganizerTeamsCSVForm
    template_name = 'teams/competitions/organizer_csv_teams.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        if self.request.user != competition.creator:
            if self.request.user not in competition.admins.all():
                return HttpResponseForbidden(status=403)
        return super(CompetitionOrganizerCSVTeams, self).dispatch(*args, **kwargs)

    # success_url = reverse('competitions:participants')
    def get_form_kwargs(self):
        kwargs = super(CompetitionOrganizerCSVTeams, self).get_form_kwargs()
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        kwargs['competition_pk'] = self.kwargs['competition_pk']
        kwargs['creator_pk'] = competition.creator.pk
        return kwargs

    def form_valid(self, form):
        try:
            competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        except ObjectDoesNotExist:
            print("Could not find a competition for that PK!")
        form.save()
        self.success_url = reverse("my_competition_participants", kwargs={'competition_id': competition.pk})
        return super(CompetitionOrganizerCSVTeams, self).form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=400)

    def get_context_data(self, **kwargs):
        context = super(CompetitionOrganizerCSVTeams, self).get_context_data(**kwargs)
        competition = Competition.objects.get(pk=self.kwargs['competition_pk'])
        context['competition'] = competition
        return context
