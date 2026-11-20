from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'OWNER'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'You do not have access to that page.')
            return redirect('dashboard')
        return super().handle_no_permission()


class OwnedQuerysetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class SafeDeleteMixin:
    protected_message = 'This record is in use and cannot be deleted.'
    success_message = 'Deleted successfully.'

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(self.get_success_url())
        messages.success(self.request, self.success_message)
        return response