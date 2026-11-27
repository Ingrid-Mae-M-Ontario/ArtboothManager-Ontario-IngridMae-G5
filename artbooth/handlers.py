from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.loader import render_to_string


def bad_request(request, exception=None):
    return render(request, '400.html', status=400)


def not_found(request, exception=None):
    return render(request, '404.html', status=404)


def permission_denied(request, exception=None):
    return render(request, '403.html', status=403)


def server_error(request):
    return HttpResponseServerError(render_to_string('500.html'))
