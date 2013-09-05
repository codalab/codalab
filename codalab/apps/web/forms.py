from django import forms
from django.forms.formsets import formset_factory
from django.contrib.auth import get_user_model
import models

User =  get_user_model()

class CompetitionForm(forms.ModelForm):
    
    def __init__(self,*args,**kwargs):
        self._user = kwargs.pop('user',None)
        super(CompetitionForm,self).__init__(*args,**kwargs)

    class Meta:
        model = models.Competition
        fields = ['title','description','has_registration','end_date']

class CompetitionPhaseForm(forms.ModelForm):

    class Meta:
        model = models.CompetitionPhase

    def save(self,commit=True):
        #self.request.FILES['dataset']
        # Possibly need async proccessing
        return super(CompetitionPhaseForm, self).save(commit)

class CompetitionParticipantForm(forms.ModelForm):
    class Meta:
        model = models.CompetitionParticipant

class CompetitionDatasetForm(forms.ModelForm):
    class Meta:
        model = models.Dataset


class RunForm(forms.ModelForm):
    class Meta:
        model = models.Run


class BundleForm(forms.ModelForm):
    class Meta:
        model = models.Bundle