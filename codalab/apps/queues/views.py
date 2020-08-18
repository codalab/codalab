from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.forms.utils import ErrorList
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from pyrabbit.http import HTTPError

from .forms import QueueForm
from .models import Queue
from . import rabbit


class QueueFormMixin(object):
    def get_success_url(self):
        return reverse('queues:list')

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(QueueFormMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs


class QueueListView(LoginRequiredMixin, ListView):
    model = Queue
    template_name = 'queues/list.html'

    def get_queryset(self):
        return Queue.objects.filter(owner=self.request.user)


class QueueCreateView(LoginRequiredMixin, QueueFormMixin, CreateView):
    model = Queue
    template_name = 'queues/form.html'
    form_class = QueueForm

    def form_valid(self, form):
        try:
            queue = form.save(commit=False)
            queue.owner = self.request.user
            if rabbit.check_user_needs_initialization(self.request.user):
                rabbit.initialize_user(self.request.user)
            queue.vhost = rabbit.create_queue(self.request.user)

            # Only save queue if things were successful
            queue.save()
            form.save_m2m()
            return HttpResponseRedirect(self.get_success_url())
        except HTTPError:
            errors = form._errors.setdefault("__all__", ErrorList())
            errors.append("Failed to create RabbitMQ queue... please report this issue on the Codalab github!")
            return self.form_invalid(form)


class QueueUpdateView(LoginRequiredMixin, QueueFormMixin, UpdateView):
    model = Queue
    template_name = 'queues/form.html'
    form_class = QueueForm


class QueueDeleteView(LoginRequiredMixin, QueueFormMixin, DeleteView):
    model = Queue
    template_name = 'queues/delete.html'

    def delete(self, request, *args, **kwargs):
        queue = self.get_object()
        if request.user != queue.owner:
            raise PermissionDenied("Cannot delete this queue, you don't own it.")
        success_url = self.get_success_url()
        queue.delete()
        return HttpResponseRedirect(success_url)
