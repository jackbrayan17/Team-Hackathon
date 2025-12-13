from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('send-emails/', views.send_emails_api, name='send_emails'),
    path('export/', views.export_excel, name='export_excel'),
]
