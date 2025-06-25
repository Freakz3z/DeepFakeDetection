from django.urls import path
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('logout/', LogoutView.as_view(next_page='/custom_auth/login/'), name='logout'),
]