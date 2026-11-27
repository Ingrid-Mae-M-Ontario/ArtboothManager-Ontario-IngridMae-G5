from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from accounts.decorators import role_required
from accounts.forms import ProfileForm, RegisterForm, StyledAuthenticationForm
from accounts.models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Registration failed. Please fix the errors below.')
        return super().form_invalid(form)


class UserLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        name = form.get_user().first_name or form.get_user().username
        messages.success(self.request, f'Welcome back, {name}!')
        return super().form_valid(form)


class UserLogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, 'You have been logged out.')
        return response


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Role.OWNER:
        return redirect('owner_dashboard')
    return redirect('assistant_dashboard')


@role_required(User.Role.OWNER)
def owner_dashboard(request):
    return render(request, 'dashboards/owner.html')


@role_required(User.Role.ASSISTANT)
def assistant_dashboard(request):
    events = request.user.assigned_events.prefetch_related('inventory__item')
    return render(request, 'dashboards/assistant.html', {'events': events})


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)