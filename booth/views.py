from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from booth.forms import EventForm, EventStockForm, ItemForm, SaleForm
from booth.mixins import OwnedQuerysetMixin, OwnerRequiredMixin, SafeDeleteMixin
from booth.models import Event, EventStock, Item, Sale
from booth.services import record_sale, void_sale


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


class AssistantEventListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Event
    template_name = 'booth/assistant_event_list.html'
    context_object_name = 'events'

    def test_func(self):
        return self.request.user.role == 'ASSISTANT'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'You do not have access to that page.')
            return redirect('dashboard')
        return super().handle_no_permission()

    def get_queryset(self):
        return Event.objects.filter(assistants=self.request.user).select_related('owner')


class EventAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    @property
    def event(self):
        if not hasattr(self, '_event'):
            self._event = get_object_or_404(Event, pk=self.kwargs['event_pk'])
        return self._event

    def test_func(self):
        user = self.request.user
        return (
            self.event.owner_id == user.pk
            or (
                user.role == 'ASSISTANT'
                and self.event.assistants.filter(pk=user.pk).exists()
            )
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'You do not have access to that page.')
            return redirect('dashboard')
        return super().handle_no_permission()


class EventStockListView(OwnerRequiredMixin, ListView):
    template_name = 'booth/stock_list.html'
    context_object_name = 'stock_items'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'OWNER':
            self.event = get_object_or_404(Event, pk=kwargs['event_pk'], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.event.stock.select_related('item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context


class EventStockCreateView(OwnerRequiredMixin, CreateView):
    form_class = EventStockForm
    template_name = 'booth/form.html'
    extra_context = {'title': 'Add event stock'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'OWNER':
            self.event = get_object_or_404(Event, pk=kwargs['event_pk'], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(event=self.event, owner=self.request.user)
        return kwargs

    def form_valid(self, form):
        form.instance.event = self.event
        messages.success(self.request, 'Event stock added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booth:stock_list', args=[self.event.pk])


class EventStockUpdateView(OwnerRequiredMixin, UpdateView):
    model = EventStock
    form_class = EventStockForm
    template_name = 'booth/form.html'
    extra_context = {'title': 'Adjust event stock'}

    def get_queryset(self):
        return EventStock.objects.filter(
            event_id=self.kwargs['event_pk'], event__owner=self.request.user,
        ).select_related('event')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(event=self.object.event, owner=self.request.user)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Event stock updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booth:stock_list', args=[self.object.event_id])


class EventStockDeleteView(OwnerRequiredMixin, SafeDeleteMixin, DeleteView):
    model = EventStock
    template_name = 'booth/confirm_delete.html'
    protected_message = 'Stock with recorded sales cannot be deleted.'
    success_message = 'Event stock deleted.'

    def get_queryset(self):
        return EventStock.objects.filter(
            event_id=self.kwargs['event_pk'], event__owner=self.request.user,
        ).select_related('event', 'item')

    def get_success_url(self):
        return reverse('booth:stock_list', args=[self.kwargs['event_pk']])


class SalesListView(EventAccessMixin, ListView):
    model = Sale
    template_name = 'booth/sales_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        queryset = Sale.objects.filter(event=self.event).select_related(
            'recorded_by', 'voided_by',
        ).prefetch_related('lines__stock__item')
        if self.request.user.pk != self.event.owner_id:
            queryset = queryset.filter(recorded_by=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['can_record_sales'] = self.event.status != Event.Status.CLOSED
        return context


class SaleCreateView(EventAccessMixin, FormView):
    form_class = SaleForm
    template_name = 'booth/sale_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.event
        return kwargs

    def form_valid(self, form):
        try:
            record_sale(
                event_id=self.event.pk,
                stock_id=form.cleaned_data['stock'].pk,
                quantity=form.cleaned_data['quantity'],
                actor=self.request.user,
            )
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, 'Sale recorded and event stock deducted.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booth:sales_list', args=[self.event.pk])


class SaleVoidView(EventAccessMixin, View):
    def post(self, request, *args, **kwargs):
        sale = get_object_or_404(Sale, pk=kwargs['pk'], event=self.event)
        try:
            void_sale(sale_id=sale.pk, actor=request.user)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            messages.success(request, 'Sale voided and stock restored.')
        return redirect('booth:sales_list', event_pk=self.event.pk)