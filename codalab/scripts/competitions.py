#!/usr/bin/env python
# Run this with the python from the CodaLab virtual environment
#

import sys
import os.path
import os
import random
import datetime
from django.utils import timezone
# This is a really, really long way around saying that if the script is in
# codalab\scripts\users.py, we need to add, ../../../codalab to the
# sys.path to find the settings
root_dir = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "codalab")
sys.path.append(root_dir)

# Set things for django configurations
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codalab.settings")

# Import the configuration
from configurations import importer
importer.install()

from django.core.files import File
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from apps.web.models import *

# Get the user model
User = get_user_model()

# Deal with time
start_date = timezone.now()

# Get a user to be the creator
guest1 = User.objects.get(username="guest1")

#
#  Start BRaTS 2012 ----
#

# BRaTS 2012
brats12_name = "MICCAI Multimodal Brain Tumor Segmentation (BRaTS) Challenge 2012"
brats12_description = """
        The BRaTS challenge is designed to gauge the current state-of-the-art in automated brain tumor segmentation 
        and to compare between different methods. It is organized in conjuction with the MICCAI 2012 conference.
        """
brats2012, _ = Competition.objects.get_or_create(
    title=brats12_name, creator=guest1, modified_by=guest1, defaults=dict(description=brats12_description))
details_category = ContentCategory.objects.get(name="Learn the Details")
participate_category = ContentCategory.objects.get(name="Participate")
pc, _ = PageContainer.objects.get_or_create(
    object_id=brats2012.id, content_type=ContentType.objects.get_for_model(Competition))
brats2012.save()

Page.objects.get_or_create(
    category=details_category, container=pc,  codename="overview",
    defaults=dict(label="Overview", rank=0,
                  html=open(os.path.join(os.path.dirname(__file__), "brats2012_overview.html")).read()))
Page.objects.get_or_create(
    category=details_category, container=pc,  codename="evaluation",
    defaults=dict(label="Evaluation", rank=1,
                  html=open(os.path.join(os.path.dirname(__file__), "brats2012_evaluation.html")).read()))
Page.objects.get_or_create(
    category=details_category, container=pc,  codename="terms_and_conditions",
    defaults=dict(rank=2, label="Terms and Conditions", html=open(os.path.join(os.path.dirname(__file__), "brats2012_terms_and_conditions.html")).read()))

Page.objects.get_or_create(
    category=details_category, container=pc,  codename="faq",
    defaults=dict(label="FAQ", rank=3, html=open(os.path.join(os.path.dirname(__file__), "brats2012_faq.html")).read()))
Page.objects.get_or_create(
    category=details_category, container=pc,  codename="key_dates",
    defaults=dict(label="Key Dates", rank=4, html=open(os.path.join(os.path.dirname(__file__), "brats2012_key_dates.html")).read()))
Page.objects.get_or_create(
    category=details_category, container=pc,  codename="organizers",
    defaults=dict(label="Organizers", rank=5, html=open(os.path.join(os.path.dirname(__file__), "brats2012_organizers.html")).read()))

Page.objects.get_or_create(
    category=participate_category, container=pc,  codename="get_data",
    defaults=dict(label="Get Data", rank=0, html=open(os.path.join(os.path.dirname(__file__), "brats2012_data.html")).read()))
Page.objects.get_or_create(category=participate_category, container=pc,
                           codename="submit_results", html="", defaults=dict(label="Submit / View Results", rank=1))

# Logo
brats2012.image = File(
    open(os.path.join(root_dir, "fixtures", "images", "brats.jpg"), 'rb'))

# Save the updates
brats2012.save()

# Phases for the competition
day_delta = datetime.timedelta(days=30)
p1date = timezone.make_aware(datetime.datetime.combine(
    datetime.date(2012, 7, 6), datetime.time()), timezone.get_current_timezone())
p2date = timezone.make_aware(datetime.datetime.combine(
    datetime.date(2012, 10, 1), datetime.time()), timezone.get_current_timezone())
p1date = timezone.make_aware(datetime.datetime.combine(
    datetime.date(2013, 7, 15), datetime.time()), timezone.get_current_timezone())
p2date = timezone.make_aware(datetime.datetime.combine(
    datetime.date(2013, 8, 30), datetime.time()), timezone.get_current_timezone())
p, created = CompetitionPhase.objects.get_or_create(
    competition=brats2012, phasenumber=1, label="Training Phase",
    start_date=p1date, max_submissions=20)
p, created = CompetitionPhase.objects.get_or_create(
    competition=brats2012, phasenumber=2, label="Competition Phase",
    start_date=p2date, max_submissions=5)
for phase in CompetitionPhase.objects.filter(competition=brats2012):
    # note that we're using the same program and truth files for both phases
    # but in reality they may be different.
    prog_file_path = os.path.join(root_dir, "media", "brats", "program.zip")
    if os.path.exists(prog_file_path):
        print("Setting program for phase: %s" % phase.label)
        phase.scoring_program = File(open(prog_file_path, 'rb'))
        phase.save()
    else:
        print("No program file set for phase: %s" % phase.label)
    reference_file_path = os.path.join(
        root_dir, "media", "brats", "testing-ref.zip")
    if os.path.exists(reference_file_path):
        print("Setting reference file for phase: %s" % phase.label)
        phase.reference_data = File(open(reference_file_path, 'rb'))
        phase.save()
    else:
        print("No reference file set for phase: %s" % phase.label)

# Score Definitions
brats_leaderboard_group_defs = {
    'patient': {'label': 'Patient Data', 'order': 1},
    'synthetic': {'label': 'Synthetic Data', 'order': 2}}

brats_leaderboard_defs = [
    # Patient data
    ('PatientDice', {'label': 'Dice'}),
    ('PatientDiceComplete',
     {'group': 'patient', 'column_group': 'PatientDice', 'label': 'Complete'}),
    ('PatientDiceCore',
     {'group': 'patient', 'column_group': 'PatientDice', 'label': 'Core'}),
    ('PatientDiceEnhancing',
     {'group': 'patient', 'column_group': 'PatientDice', 'label': 'Enhancing'}),
    ('PatientSensitivity', {'label': 'Sensitivity'}),
    ('PatientSensitivityComplete',
     {'group': 'patient', 'column_group': 'PatientSensitivity', 'label': 'Complete'}),
    ('PatientSensitivityCore',
     {'group': 'patient', 'column_group': 'PatientSensitivity', 'label': 'Core'}),
    ('PatientSensitivityEnhancing',
     {'group': 'patient', 'column_group': 'PatientSensitivity', 'label': 'Enhancing'}),
    ('PatientSpecificity', {'label': 'Specificity'}),
    ('PatientSpecificityComplete',
     {'group': 'patient', 'column_group': 'PatientSpecificity', 'label': 'Complete'}),
    ('PatientSpecificityCore',
     {'group': 'patient', 'column_group': 'PatientSpecificity', 'label': 'Core'}),
    ('PatientSpecificityEnhancing',
     {'group': 'patient', 'column_group': 'PatientSpecificity', 'label': 'Enhancing'}),
    ('PatientHausdorff', {'label': 'Hausdorff'}),
    ('PatientHausdorffComplete',
     {'group': 'patient', 'column_group': 'PatientHausdorff', 'label': 'Complete', 'sort': 'asc'}),
    ('PatientHausdorffCore',
     {'group': 'patient', 'column_group': 'PatientHausdorff', 'label': 'Core', 'sort': 'asc'}),
    ('PatientHausdorffEnhancing', {'group': 'patient', 'column_group':
     'PatientHausdorff', 'label': 'Enhancing', 'sort': 'asc'}),
    ('PatientKappa', {'group': 'patient', 'label': 'Kappa'}),
    ('PatientRank', {'label': 'Rank'}),
    ('PatientRankComplete',  {'group': 'patient', 'column_group': 'PatientRank', 'label': 'Complete',
                              'computed': {'operation': 'Avg', 'fields': ('PatientDiceComplete', 'PatientSensitivityComplete', 'PatientSpecificityComplete')}}),
    ('PatientRankCore',      {'group': 'patient', 'column_group': 'PatientRank', 'label': 'Core',
                              'computed': {'operation': 'Avg', 'fields': ('PatientDiceCore', 'PatientSensitivityCore', 'PatientSpecificityCore')}}),
    ('PatientRankEnhancing', {'group': 'patient', 'column_group': 'PatientRank', 'label': 'Enhancing',
                              'computed': {'operation': 'Avg', 'fields': ('PatientDiceEnhancing', 'PatientSensitivityEnhancing', 'PatientSpecificityEnhancing')}}),
    ('PatientRankOverall', {'group': 'patient', 'label': 'Overall Rank', 'selection_default': 1,
                            'computed': {'operation': 'Avg', 'fields': ('PatientDiceComplete', 'PatientSensitivityComplete', 'PatientSpecificityComplete',
                                                                        'PatientDiceEnhancing', 'PatientSensitivityEnhancing', 'PatientSpecificityEnhancing',
                                                                        'PatientDiceEnhancing', 'PatientSensitivityEnhancing', 'PatientSpecificityEnhancing')}}),
    # Synthetic data
    ('SyntheticDice', {'label': 'Dice'}),
    ('SyntheticDiceComplete',
     {'group': 'synthetic', 'column_group': 'SyntheticDice', 'label': 'Complete'}),
    ('SyntheticDiceCore',
     {'group': 'synthetic', 'column_group': 'SyntheticDice', 'label': 'Core'}),
    ('SyntheticSensitivity', {'label': 'Sensitivity'}),
    ('SyntheticSensitivityComplete',
     {'group': 'synthetic', 'column_group': 'SyntheticSensitivity', 'label': 'Complete'}),
    ('SyntheticSensitivityCore',
     {'group': 'synthetic', 'column_group': 'SyntheticSensitivity', 'label': 'Core'}),
    ('SyntheticSpecificity', {'label': 'Specificity'}),
    ('SyntheticSpecificityComplete',
     {'group': 'synthetic', 'column_group': 'SyntheticSpecificity', 'label': 'Complete'}),
    ('SyntheticSpecificityCore',
     {'group': 'synthetic', 'column_group': 'SyntheticSpecificity', 'label': 'Core'}),
    ('SyntheticHausdorff', {'label': 'Hausdorff'}),
    ('SyntheticHausdorffComplete', {'group': 'synthetic', 'column_group':
     'SyntheticHausdorff', 'label': 'Complete', 'sort': 'asc'}),
    ('SyntheticHausdorffCore',
     {'group': 'synthetic', 'column_group': 'SyntheticHausdorff', 'label': 'Core', 'sort': 'asc'}),
    ('SyntheticKappa', {'group': 'synthetic', 'label': 'Kappa'}),
    ('SyntheticRank', {'label': 'Rank'}),
    ('SyntheticRankComplete', {'group': 'synthetic', 'column_group': 'SyntheticRank', 'label': 'Complete',
                               'computed': {'operation': 'Avg', 'fields': ('SyntheticDiceComplete', 'SyntheticSensitivityComplete', 'SyntheticSpecificityComplete')}}),
    ('SyntheticRankCore',     {'group': 'synthetic', 'column_group': 'SyntheticRank', 'label': 'Core',
                               'computed': {'operation': 'Avg', 'fields': ('SyntheticDiceCore', 'SyntheticSensitivityCore', 'SyntheticSpecificityCore')}}),
    ('SyntheticRankOverall',  {'group': 'synthetic', 'label': 'Overall Rank', 'selection_default': 1,
                               'computed': {'operation': 'Avg', 'fields': ('SyntheticDiceComplete', 'SyntheticSensitivityComplete', 'SyntheticSpecificityComplete',
                                                                           'SyntheticDiceCore', 'SyntheticSensitivityCore', 'SyntheticSpecificityCore')}})]

brats_groups = {}
for (key, vals) in brats_leaderboard_group_defs.items():
    rg, cr = SubmissionResultGroup.objects.get_or_create(
        competition=brats2012,
        key=key,
        defaults=dict(label=vals['label'],
                      ordering=vals['order']),)
    brats_groups[rg.key] = rg
    # All phases have the same leaderboard so add the group to each of them
    for gp in brats2012.phases.all():
        rgp, crx = SubmissionResultGroupPhase.objects.get_or_create(
            phase=gp, group=rg)

brats_column_groups = {}
brats_score_defs = {}
for key, vals in brats_leaderboard_defs:
    if 'group' not in vals:
        # Define a new grouping of scores
        s, cr = SubmissionScoreSet.objects.get_or_create(
            competition=brats2012,
            key=key,
            defaults=dict(label=vals['label']))
        brats_column_groups[key] = s
    else:
        # Create the score definition
        is_computed = 'computed' in vals
        sort_order = 'desc' if 'sort' not in vals else vals['sort']
        sdefaults = dict(label=vals['label'], numeric_format="2",
                         show_rank=not is_computed, sorting=sort_order)
        if 'selection_default' in vals:
            sdefaults['selection_default'] = vals['selection_default']

        sd, cr = SubmissionScoreDef.objects.get_or_create(
            competition=brats2012,
            key=key,
            computed=is_computed,
            defaults=sdefaults)
        if is_computed:
            sc, cr = SubmissionComputedScore.objects.get_or_create(
                scoredef=sd, operation=vals['computed']['operation'])
            for f in vals['computed']['fields']:
                # Note the lookup in brats_score_defs. The assumption is that computed properties are defined in
                # brats_leaderboard_defs after the fields they reference.
                SubmissionComputedScoreField.objects.get_or_create(
                    computed=sc, scoredef=brats_score_defs[f])
        brats_score_defs[sd.key] = sd

        # Associate the score definition with its column group
        if 'column_group' in vals:
            gparent = brats_column_groups[vals['column_group']]
            g, cr = SubmissionScoreSet.objects.get_or_create(
                competition=brats2012,
                parent=gparent,
                key=sd.key,
                defaults=dict(scoredef=sd, label=sd.label))
        else:
            g, cr = SubmissionScoreSet.objects.get_or_create(
                competition=brats2012,
                key=sd.key,
                defaults=dict(scoredef=sd, label=sd.label))

        # Associate the score definition with its result group
        sdg, cr = SubmissionScoreDefGroup.objects.get_or_create(
            scoredef=sd, group=brats_groups[vals['group']])

# Participant statuses, if they haven't been created before
statuses = ParticipantStatus.objects.all()

# Participants for the competition
participants = [(statuses[i - 2], User.objects.get(username="guest%d" % i))
                for i in range(2, len(statuses) + 2)]

# Participant statuses, if they haven't been created before
statuses = ParticipantStatus.objects.all()

# Add participants to the competition with random statuses
for status, participant in participants:
    print("Adding %s to competition %s with status %s" % (participant, brats2012, status))
    resulting_participant, created = CompetitionParticipant.objects.get_or_create(
        user=participant, competition=brats2012, defaults={'status': status})
#
#  End BRaTS 2012 ----
#

#
# Spine Localization
#
spine_name = "Spine Localization Example"
spine_description = """
        Test for server side execution of evaluation program.
"""
spine, created = Competition.objects.get_or_create(
    title=spine_name, creator=guest1, modified_by=guest1,
    description=spine_description, has_registration=True)

details_category = ContentCategory.objects.get(name="Learn the Details")
participate_category = ContentCategory.objects.get(name="Participate")
pc, _ = PageContainer.objects.get_or_create(
    object_id=spine.id, content_type=ContentType.objects.get_for_model(Competition))
spine.save()

# Logo
spine.image = File(
    open(os.path.join(root_dir, "fixtures", "images", "spine.jpg"), 'rb'))

# Save updates
spine.save()

# Phases for the competition
day_delta = datetime.timedelta(days=30)
for phase in [1, 2, 3]:
    phase_start = start_date + (day_delta * phase)
    p, created = CompetitionPhase.objects.get_or_create(
        competition=spine, phasenumber=phase, label="Phase %d" % phase,
        start_date=phase_start, max_submissions=4)

# Participants for the competition
participants = [User.objects.get(username="guest%d" % random.choice(list(range(1, 10))))
                for i in range(random.choice(list(range(1, 5))))]
# print participants

# Participant statuses, if they haven't been created before
statuses = ParticipantStatus.objects.all()
# print statuses

# Add participants to the competition with random statuses
for participant in participants:
    status = random.choice(statuses)
    # print "Adding %s to competition %s with status %s" % (participant,
    # spine, status)
    resulting_participant, created = CompetitionParticipant.objects.get_or_create(
        user=participant, competition=spine,
        defaults={'status': status})
#
#  End Spine Localization ----
#

#
# Single-phase competition
#


def create_single_phase_sample():
    title = "Single-phase competition example"
    description = "This is an example of a single-phase competition."
    competition, created = Competition.objects.get_or_create(
        title=title, creator=guest1, modified_by=guest1, description=description)
    competition.save()

    # Note: no logo specified on purpose

    # The one phase of the competition
    phase_start = timezone.now()
    phase, created = CompetitionPhase.objects.get_or_create(
        competition=competition, phasenumber=1, label="Game On",
        start_date=phase_start, max_submissions=10)

    # Participants for the competition
    participants = [User.objects.get(username="guest%d" % i)
                    for i in range(1, 5)]
    # Participant statuses, if they haven't been created before
    ParticipantStatus.objects.all()
    # Add participants to the competition with random statuses
    for participant in participants:
        status = ParticipantStatus.objects.get(
            codename=ParticipantStatus.PENDING)
        resulting_participant, created = CompetitionParticipant.objects.get_or_create(
            user=participant, competition=competition,
            defaults={'status': status})
#
#  End single-phase competition ----
#
create_single_phase_sample()
