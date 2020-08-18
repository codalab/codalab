'''
This file contains utilities for competitions
'''
import datetime
import sys

from random import randint, shuffle, sample

from django.db.models import Count
from django.db.models import Q
from django.utils.timezone import now

from apps.web.models import Competition, CompetitionSubmission


def get_most_popular_competitions(min_participants=400, limit=5, fill_in=True):
    today = datetime.datetime.today()

    sub_query = Competition.objects.annotate(num_participants=Count('participants')) \
        .filter(num_participants__gte=min_participants)

    competitions = Competition.objects.filter(published=True) \
       .filter(Q(end_date__gte=today) | Q(end_date=None)) \
       .filter(pk__in=sub_query) \
       .order_by('?') \
       .select_related('creator')[:limit]
    # shuffle works in place, so turn competitions into list and shuffle it by reference
    competitions = list(competitions)
    comp_count = len(competitions)

    if comp_count < limit and fill_in:
        existing_pks = [c.pk for c in competitions]
        random_competitions = Competition.objects.filter(published=True).exclude(pk__in=existing_pks) \
            .annotate(num_participants=Count('participants')) \
            .select_related('creator') \
            .order_by('-num_participants')[:10]
        try:
            # Had to convert to set/list in Py3
            competitions += sample(set(random_competitions), limit - comp_count)
        except ValueError:
            # Eeep! We don't even have $limit competitions to choose from
            competitions += list(random_competitions)
    shuffle(competitions)
    return competitions


def get_featured_competitions(popular_competitions_to_filter=None, limit=5):
    featured_competitions = []

    if popular_competitions_to_filter:
        # Exclude popular competitions, so we don't show them near featured
        popular_filter_pks = [c.pk for c in popular_competitions_to_filter]
    else:
        popular_competitions_to_filter = []
        popular_filter_pks = []

    a_month_ago = now() - datetime.timedelta(days=30)
    a_month_from_now = now() + datetime.timedelta(days=30)
    seven_days_ago = now() - datetime.timedelta(days=7)

    # Filter out competitions that don't have a submission from the last week
    if not ('test' in sys.argv or any('py.test' in arg for arg in sys.argv)):
        recent_submissions = CompetitionSubmission.objects.filter(phase__competition__published=True, submitted_at__gte=seven_days_ago).distinct('phase__competition')
    else:
        # DISTINCT isn't impelemented on sqlite for tests, so ignore that in this case
        recent_submissions = CompetitionSubmission.objects.filter(phase__competition__published=True, submitted_at__gte=seven_days_ago)
    recent_submissions = recent_submissions.select_related('phase', 'phase__competition')
    for sub in recent_submissions:
        # We have a recent submission, so check that competition is either active or has upcoming phase change
        competition = sub.phase.competition
        phase_change_within_a_month = competition.phases.filter(
            start_date__gte=now(),
            start_date__lte=a_month_from_now
        ).exists()
        if competition.start_date:
            recently_started = competition.start_date < a_month_ago
        else:
            recently_started = False
        if recently_started or phase_change_within_a_month and competition.pk not in popular_filter_pks:
            if competition not in featured_competitions and competition not in popular_competitions_to_filter:
                featured_competitions.append(competition)

    # Fill out competitions if we're missing any (or truncate if too much)
    featured_comp_count = len(featured_competitions)
    if featured_comp_count < limit:
        existing_pks = [c.pk for c in featured_competitions]
        random_competitions = Competition.objects.filter(published=True) \
            .select_related('creator') \
            .exclude(pk__in=popular_filter_pks) \
            .exclude(pk__in=existing_pks)[:50]
        try:
            # Had to convert to set for Py3
            featured_competitions += sample(set(random_competitions), limit - featured_comp_count)
        except ValueError:
            # Eeep! We don't even have $limit competitions to choose from
            featured_competitions += list(random_competitions)
    elif featured_comp_count > limit:
        featured_competitions = featured_competitions[:limit]

    # Random order each time
    shuffle(featured_competitions)

    for competition in featured_competitions:
        competition.num_participants = competition.get_participant_count

    return featured_competitions
