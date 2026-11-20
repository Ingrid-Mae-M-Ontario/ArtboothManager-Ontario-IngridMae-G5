from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('booth/', include('booth.urls')),
    path('', include('accounts.urls')),
]