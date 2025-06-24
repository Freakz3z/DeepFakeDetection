from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('history/', views.history_view, name='history'),
    path('history/delete/<int:record_id>/', views.delete_record, name='delete_record'),
]