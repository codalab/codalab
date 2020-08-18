import logging
import os
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.functional import cached_property
from django import template
import apps.web as web
from apps.web.utils import PublicStorage, BundleStorage, get_object_base_url
from datetime import datetime, timedelta

register = template.Library()
User = settings.AUTH_USER_MODEL
logger = logging.getLogger(__name__)


def get_competition_teams(competition):
    team_list=Team.objects.filter(
        competition=competition,
        status=TeamStatus.objects.get(codename="approved"),
    ).all()
    return team_list


def get_competition_pending_teams(competition):
    team_list=Team.objects.filter(
        competition=competition,
        status=TeamStatus.objects.get(codename="pending"),
    ).select_related("status").all()

    return team_list


def get_team_pending_membership(team):
    requests = TeamMembership.objects.filter(
        team=team,
        is_request=True,
        status=TeamMembershipStatus.objects.get(codename="pending"),
    ).select_related("user").all()
    return requests


def get_competition_deleted_teams(competition):
    team_list=Team.objects.filter(
        competition=competition,
        status=TeamStatus.objects.get(codename="deleted"),
    ).all()

    return team_list


def get_competition_user_teams(competition,user):
    team_list=Team.objects.filter(
        competition=competition,
        status=TeamStatus.objects.get(codename="approved"),
        creator=user.user,
    ).all()
    if len(team_list)==0:
        team_list=None
    else:
        team_list=team_list[0]
    return team_list


def get_competition_user_pending_teams(competition,user):
    team_list=Team.objects.filter(
        competition=competition,
        status=TeamStatus.objects.get(codename="pending"),
        creator=user.user,
    ).all()
    if len(team_list)==0:
        team_list=None
    else:
        team_list=team_list[0]
    return team_list


def get_user_requests(user, competition):
    team_list = get_competition_teams(competition)
    user_requests = TeamMembership.objects.filter(
        user=user.user,
        team__in=team_list,
    ).all()
    return user_requests


def get_allowed_teams(user,competition):
    # TODO: Remove teams where user already have a request
    return get_competition_teams(competition)


# def get_user_team(user, competition):
def get_user_team(participant, competition):
    # This function just gets user's created teams that are approved
    # and returns the first one or None
    user_created_teams = Team.objects.filter(competition=competition, creator=participant.user, status__codename='approved').select_related('status')
    # If we have user created teams
    if user_created_teams is not None and len(user_created_teams) > 0:
        return user_created_teams[0]
    else:
        # Else if no user created teams
        user_approved_team_memberships = list(participant.user.team_memberships.filter(status__codename='approved').select_related('team', 'status'))
        user_approved_active_teams = [membership for membership in user_approved_team_memberships if membership.is_active]
        if user_approved_active_teams is not None and len(user_approved_active_teams) > 0:
            return user_approved_active_teams[0].team
    return None

def get_team_submissions(team, phase=None):
    if phase is None:
        t_s = web.models.CompetitionSubmission.objects.filter(phase=phase, team=team)
    else:
        t_s = web.models.CompetitionSubmission.objects.filter(team=team)

    return t_s


def get_last_team_submissions(team, days=1):
    return web.models.CompetitionSubmission.objects.filter(team=team, submitted_at__gte=datetime.now()-timedelta(days))


def get_team_submissions_inf(team, phase):

    submissions = web.models.CompetitionSubmission.objects.filter(
        team=team,
        phase=phase
    ).select_related('status').order_by('-submitted_at')

    # find which submission is in the leaderboard, if any and only if phase allows seeing results.
    id_of_submission_in_leaderboard = -1
    if phase and not phase.is_blind:
        leaderboard_entry = web.models.PhaseLeaderBoardEntry.objects.filter(
            board__phase=phase,
            result__team=team
        ).select_related('result', 'result__participant')
        if leaderboard_entry:
            id_of_submission_in_leaderboard = leaderboard_entry[0].result.pk
    submission_info_list = []
    for submission in submissions:
        submission_info = {
            'id': submission.id,
            'number': submission.submission_number,
            'username': submission.participant.user.username,
            'filename': submission.get_filename(),  # left as call for legacy update of readable_filename on subs.
            'submitted_at': submission.submitted_at,
            'status_name': submission.status.name,
            'is_finished': submission.status.codename == 'finished',
            'is_in_leaderboard': submission.id == id_of_submission_in_leaderboard,
            'exception_details': submission.exception_details,
            'description': submission.description,
            'team_name': submission.team_name,
            'method_name': submission.method_name,
            'method_description': submission.method_description,
            'project_url': submission.project_url,
            'publication_url': submission.publication_url,
            'bibtex': submission.bibtex,
            'organization_or_affiliation': submission.organization_or_affiliation,
            'is_public': submission.is_public,
            'score': submission.get_default_score(),
        }
        submission_info_list.append(submission_info)

    return submission_info_list


def get_available_participants(competition):
    return []


class TeamStatus(models.Model):
    UNKNOWN = 'unknown'
    DENIED = 'denied'
    APPROVED = 'approved'
    PENDING = 'pending'
    DELETED = 'deleted'
    name = models.CharField(max_length=30)
    codename = models.CharField(max_length=30,unique=True)
    description = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Team(models.Model):
    """ This is the base team. """
    class Meta:
        unique_together = (('name', 'competition'),)

    def __unicode__(self):
        return "[%s] %s - %s" % (self.status.codename, self.competition.title, self.name)

    name = models.CharField(max_length=100, null=False, blank=False)
    competition = models.ForeignKey('web.Competition')
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to='team_logo', storage=PublicStorage, null=True, blank=True, verbose_name="Logo")
    image_url_base = models.CharField(max_length=255)
    allow_requests = models.BooleanField(default=True, verbose_name="Allow requests")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='team_creator')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='TeamMembership', blank=True, null=True, related_name='teams')
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(TeamStatus, null=True)
    reason = models.CharField(max_length=100,null=True,blank=True)

    def save(self, *args, **kwargs):
        # Make sure the image_url_base is set from the actual storage implementation
        # get_object_base_url was due to differences in boto vs boto3. A utility function seemed the best route to
        # handle different storage implementations
        self.image_url_base = get_object_base_url(self, 'image')
        self.last_modified=now()

        if self.status is None:
            self.status = TeamStatus.objects.get(codename=TeamStatus.PENDING)

        # Do the real save
        return super(Team,self).save(*args,**kwargs)

    @cached_property
    def image_url(self):
        # Return the transformed image_url
        if self.image:
            return os.path.join(self.image_url_base, self.image.name)
        return None

    @cached_property
    def active_members(self):
        return self.get_members("approved")

    @cached_property
    def active_members_count(self):
        return len(self.get_members("approved")) + 1

    @cached_property
    def active_requests(self):
        return self.get_members("pending")

    def has_applied(self, user):
        for member in self.get_members("pending"):
            if member.user == user:
                return True
        return False

    def is_member(self, user):
        for member in self.get_members("approved"):
            if member.user == user:
                return True
        return False

    @property
    def is_admin(self, user):
        return self.creator==user

    def get_members(self, status):
        requests = TeamMembership.objects.filter(
            team=self,
            is_request=True,
            status=TeamMembershipStatus.objects.get(codename=status),
        ).select_related("user").all()

        members=[]
        for member in requests:
            if member.is_active:
                members.append(member)

        return members


class TeamMembershipStatus(models.Model):
    UNKNOWN = 'unknown'
    REJECTED = 'rejected'
    APPROVED = 'approved'
    PENDING = 'pending'
    CANCELED = 'canceled'
    name = models.CharField(max_length=30)
    codename = models.CharField(max_length=30,unique=True)
    description = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class TeamMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='team_memberships')
    team = models.ForeignKey(Team)
    is_invitation = models.BooleanField(default=False)
    is_request = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Start Date (UTC)")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="End Date (UTC)")
    message = models.TextField(null=True, blank=True)
    status = models.ForeignKey(TeamMembershipStatus, null=True)
    reason = models.CharField(max_length=100,null=True,blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.team_id, self.user_id)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        other_memberships = TeamMembership.objects.filter(user=self.user, team__competition=self.team.competition).exclude(pk=self.pk)
        if len(other_memberships) != 0:
            logger.info("Removing user: {0} from other memberships in competition: {1}".format(self.user, self.team.competition))
            other_memberships.delete()
        super(TeamMembership, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    @property
    def is_active(self):
        if self.start_date is not None and now() < self.start_date:
            return False
        if self.end_date is not None and now() > self.end_date:
            return False

        return True
