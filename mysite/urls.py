"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# mysite/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from custom_auth import views as custom_auth_views

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', custom_auth_views.register, name='register'),
    path('admin/', admin.site.urls),
    path('', include('polls.urls')),
    path('history/', custom_auth_views.history_view, name='history'),
    path('history/delete/<int:record_id>/', custom_auth_views.delete_record, name='delete_record'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 
