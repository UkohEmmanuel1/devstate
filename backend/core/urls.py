from django.urls import path
from . import views
urlpatterns=[path('health/',views.health),path('projects/',views.projects),path('projects/scan/',views.scan_projects),path('events/',views.events),path('events/create/',views.create_event),path('focus/',views.focus),path('focus/start/',views.focus_start),path('focus/end/',views.focus_end),path('notifications/test/',views.notification_test),path('snapshots/',views.snapshots)]
