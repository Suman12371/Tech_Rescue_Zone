from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm


app_name="TechRescueZoneApp"
urlpatterns = [
    path('home', views.home_view, name='home'),
    path('', views.register_view, name='register'),
    path('register/', views.register_view, name='register'),
     path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    
   
    
]