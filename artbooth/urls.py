from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('booth/', include('booth.urls')),
    path('', include('accounts.urls')),
]

handler400 = 'artbooth.handlers.bad_request'
handler403 = 'artbooth.handlers.permission_denied'
handler404 = 'artbooth.handlers.not_found'
handler500 = 'artbooth.handlers.server_error'