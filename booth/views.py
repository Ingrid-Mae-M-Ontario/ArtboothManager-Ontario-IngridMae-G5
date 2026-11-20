from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from booth.forms import EventForm, ItemForm
from booth.mixins import OwnedQuerysetMixin, OwnerRequiredMixin, SafeDeleteMixin
from booth.models import Event, Item


class ItemListView(OwnerRequiredMixin, OwnedQuerysetMixin, ListView):
    model = Item
    template_name = 'booth/item_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        return qs.filter(name__icontains=q) if q else qs


class ItemCreateView(OwnerRequiredMixin, CreateView):
    form_class = ItemForm
    template_name = 'booth/form.html'
    success_url = reverse_lazy('booth:item_list')
    extra_context = {'title': 'Add item'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Item added.')
        return super().form_valid(form)


class ItemUpdateView(OwnerRequiredMixin, OwnedQuerysetMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'booth/form.html'
    success_url = reverse_lazy('booth:item_list')
    extra_context = {'title': 'Edit item'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Item updated.')
        return super().form_valid(form)


class ItemDeleteView(OwnerRequiredMixin, OwnedQuerysetMixin, SafeDeleteMixin, DeleteView):
    model = Item
    template_name = 'booth/confirm_delete.html'
    success_url = reverse_lazy('booth:item_list')
    protected_message = 'This item is used in event stock or sales. Deactivate it instead of deleting.'
    success_message = 'Item deleted.'


class EventListView(OwnerRequiredMixin, OwnedQuerysetMixin, ListView):
    model = Event
    template_name = 'booth/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('assistants')
        status = self.request.GET.get('status', '')
        return qs.filter(status=status) if status in Event.Status.values else qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Event.Status.choices
        return context


class EventCreateView(OwnerRequiredMixin, CreateView):
    form_class = EventForm
    template_name = 'booth/form.html'
    success_url = reverse_lazy('booth:event_list')
    extra_context = {'title': 'Create event'}

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Event created.')
        return super().form_valid(form)


class EventUpdateView(OwnerRequiredMixin, OwnedQuerysetMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'booth/form.html'
    success_url = reverse_lazy('booth:event_list')
    extra_context = {'title': 'Edit event'}

    def form_valid(self, form):
        messages.success(self.request, 'Event updated.')
        return super().form_valid(form)


class EventDeleteView(OwnerRequiredMixin, OwnedQuerysetMixin, SafeDeleteMixin, DeleteView):
    model = Event
    template_name = 'booth/confirm_delete.html'
    success_url = reverse_lazy('booth:event_list')
    protected_message = 'This event has recorded sales and cannot be deleted. Close it instead.'
    success_message = 'Event deleted.'