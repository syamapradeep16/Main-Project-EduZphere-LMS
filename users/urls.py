from django.urls import path
from .views import *

urlpatterns = [

    path('', home, name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('dashboard/',dashboard, name='dashboard'),
    path('profile/',profile, name='profile'),
    path('register/',register, name='register'),
    path('login/',user_login, name='login'),
    path('logout/',user_logout, name='logout'),
    path('student_list',student_list,name='student_list'),
    path('instructors/', instructor_list, name='instructor_list'),
    path('instructors/assign/<int:user_id>/', assign_course, name='assign_course'),
    path('instructors/remove/<int:course_id>/',remove_course, name='remove_course'),
    path('workshops/', workshops, name='workshops'),
    path('backup/download/', system_backup_download, name='system_backup'),
    path('inquiries/', inquiry_list, name='inquiry_list'),
]
