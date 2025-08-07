from django.urls import path
from . import views as vws

urlpatterns = [
    path('create/', vws.create_saving, name='create-saving'),
    path('my-history/', vws.savings_history, name='user-saving-history'),
    path('withdraw/<int:pk>/', vws.withdraw_saving, name='withdraw-saving'),
    path('dashboard/', vws.dashboard, name='dashboard'),
    path('notifications/<int:pk>/',vws.read_notification, name='read_notification')


]



