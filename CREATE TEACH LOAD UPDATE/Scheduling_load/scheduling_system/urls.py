from django.urls import path
from .views import (
    home,
    create_teaching_load,
    search_instructors,teaching_load,instructor_details,search_courses,course_details,
    room_utilization,
    search_rooms,
    room_details,search_program,get_program_schedule,get_program_list,
    search_programs, program_details, save_program_schedule,search_stored_data,stored_data_details,program_by_section,stored_time_details,get_instructor_schedule,get_instructor_load,
    filter_programs,get_section_details,search_section,get_room_suggestions,get_room_schedule
)

urlpatterns = [
    path('', home, name='index'),
    path('create_teaching_load/', create_teaching_load, name='create_teaching_load'),
    path('teaching_load/',teaching_load,name='teaching_load'),
    path('program_by_section/',program_by_section,name='program_by_section'),
    path('search_instructors/', search_instructors, name='search_instructors'),
    path('teaching_load/',teaching_load,name='teaching_load'),
    path('details/', instructor_details, name='instructor_details'),
    path('search_courses/',search_courses, name='search_courses'),
    path('course_details/',course_details,name='course_details'),
    path('room-utilization/',room_utilization, name='room_utilization'),
    path('search_rooms/', search_rooms, name='search_rooms'),
    path('room_details/', room_details, name='room_details'),
    # path('schedule-room/',schedule_room, name='schedule_room'),
    path('search_programs/', search_programs, name='search_programs'),
    path('program_details/', program_details, name='program_details'),
    path('save_program_schedule/', save_program_schedule, name='save_program_schedule'),
    path('search/', search_stored_data, name='search_stored_data'),
    path('stored_data_details/',stored_data_details,name='stored_data_details'),
    path('stored_time_details/',stored_time_details,name='stored_time_details'),
    path('get_instructor_schedule/',get_instructor_schedule,name='get_instructor_schedule'),
    path('get_instructor_load/', get_instructor_load, name='get_instructor_load'),
    path('search_section/', search_section, name='search_section'),
    path('get_section_details/', get_section_details, name='get_section_details'),
    path('filter_programs/', filter_programs, name='filter_programs'),
    path('search_program/', search_program, name='search_program'),
    path('get_program_schedule/', get_program_schedule, name='get_program_schedule'),
    path('get_program_list/', get_program_list, name='get_program_list'),
    path('get-room-suggestions/', get_room_suggestions, name='get_room_suggestions'),
    path('get-room-schedule/', get_room_schedule, name='get_room_schedule')
]
