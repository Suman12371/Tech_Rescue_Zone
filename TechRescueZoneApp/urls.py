# from django.urls import path
# from django.contrib.auth import views as auth_views
# from . import views
# from django.views.generic.edit import CreateView
# from django.contrib.auth.forms import UserCreationForm
# from django.conf.urls.static import static
# from django.conf import settings

# app_name="TechRescueZoneApp"
# urlpatterns = [
#     path('', views.home_view, name='home'),
#     path('home', views.home_view, name='home'),
#     # path('', views.register_view, name='register'),
#     path('register/', views.register_view, name='register'),
#     path('login/', views.login_view, name='login'),
#     path('logout/', views.logout_view, name='logout'),
    
#     path('verify_email/', views.verify_email, name='verify_email'),
    
#     path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
#     path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
#     path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
#     path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
   
    
    
    
    
#     path('hardware_list', views.hardware_list, name='hardware_list'),
#     path('<int:hardware_id>/', views.hardware_detail, name='hardware_detail'),
#     path('add/', views.add_hardware, name='add_hardware'),
#     path('edit/<int:hardware_id>/', views.edit_hardware, name='edit_hardware'),
#     path('delete/<int:hardware_id>/', views.delete_hardware, name='delete_hardware'),
#     path('add-to-cart/<int:hardware_id>/', views.add_to_cart, name='add_to_cart'),
#     path('cart/', views.cart, name='cart'),
#     path('checkout/', views.checkout, name='checkout'),
#     path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
#     path('solution_list', views.solution_list, name='solution_list'),
#     path('<int:solution_id>/', views.solution_detail, name='solution_detail'),
#     path('create/', views.create_solution, name='create_solution'),
#     path('<int:solution_id>/steps/', views.add_solution_steps, name='add_solution_steps'),
#     path('<int:solution_id>/edit/', views.edit_solution, name='edit_solution'),
#     path('<int:solution_id>/edit/steps/', views.edit_solution_steps, name='edit_solution_steps'),
#     path('<int:solution_id>/delete/', views.delete_solution, name='delete_solution'),
#     path('<int:solution_id>/like/', views.like_solution, name='like_solution'),
    
    
#     path('chat_list', views.chat_list, name='chat_list'),
#     path('<int:conversation_id>/', views.chat_detail, name='chat_detail'),
#     path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
#     path('<int:conversation_id>/messages/', views.get_new_messages, name='get_new_messages'),
    
    
#     path('notification_list', views.notification_list, name='notification_list'),
#     path('<int:notification_id>/mark-read/', views.mark_as_read, name='mark_notification_read'),
#     path('mark-all-read/', views.mark_all_as_read, name='mark_all_notifications_read'),
    
    
#     path('process/<int:order_id>/', views.payment_process, name='payment_process'),
#     path('methods/', views.payment_methods, name='payment_methods'),
#     path('methods/add/', views.add_payment_method, name='add_payment_method'),
#     path('methods/<int:method_id>/delete/', views.delete_payment_method, name='delete_payment_method'),
#     path('methods/<int:method_id>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    
    
# ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.conf.urls.static import static
from django.conf import settings

app_name="TechRescueZoneApp"
urlpatterns = [
    path('', views.home_view, name='home'),
    path('home', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('verify_email/', views.verify_email, name='verify_email'),
    
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
   
    # profile
    path('user_profile/', views.user_profile, name='user_profile'),
    path('export_profile/', views.export_profile, name='export_profile'),
    

    # Hardware 
    
    path('hardware/', views.hardware_list, name='hardware_list'),
    path('hardware/<int:hardware_id>/', views.hardware_detail, name='hardware_detail'),
    path('hardware/add/', views.add_hardware, name='add_hardware'),
    path('hardware/edit/<int:hardware_id>/', views.edit_hardware, name='edit_hardware'),
    path('hardware/delete/<int:hardware_id>/', views.delete_hardware, name='delete_hardware'),
    
    # Solution URLs - with 'solutions/' prefix to avoid conflicts
    path('solutions/', views.solution_list, name='solution_list'),
    path('solutions/<int:solution_id>/', views.solution_detail, name='solution_detail'),
    path('solutions/create/', views.create_solution, name='create_solution'),
    path('solutions/<int:solution_id>/steps/', views.add_solution_steps, name='add_solution_steps'),
    path('solutions/<int:solution_id>/edit/', views.edit_solution, name='edit_solution'),
    path('solutions/<int:solution_id>/edit/steps/', views.edit_solution_steps, name='edit_solution_steps'),
    path('solutions/<int:solution_id>/delete/', views.delete_solution, name='delete_solution'),
    path('solutions/<int:solution_id>/like/', views.like_solution, name='like_solution'),

    
   
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

