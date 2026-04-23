from django.urls import path

from . import views

app_name = 'schedules'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('list/', views.ScheduleListView.as_view(), name='list'),
    path('my-schedule/', views.MyScheduleListView.as_view(), name='my_schedule'),
    path('api/events/', views.ScheduleEventsApiView.as_view(), name='events_api'),
    path('api/locations/', views.LocationOptionsApiView.as_view(), name='locations_api'),
    path('api/personnel/', views.PersonnelOptionsApiView.as_view(), name='personnel_api'),
    path('api/create/', views.ScheduleCreateView.as_view(), name='create_shift'),
    path('api/<int:schedule_id>/update/', views.ScheduleUpdateView.as_view(), name='update_shift'),
    path('api/<int:schedule_id>/delete/', views.ScheduleDeleteView.as_view(), name='delete_shift'),
    path('api/<int:schedule_id>/move/', views.ScheduleMoveView.as_view(), name='move_shift'),
]
