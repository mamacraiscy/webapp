from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q,Prefetch
from django.views.decorators.csrf import csrf_exempt
from .models import InstructorData, InstructorCourse, Program, Room, Campus, Building, Room, ProgramSchedule, Schedule
from .forms import ProgramScheduleForm
from datetime import datetime
from django.utils import timezone
import traceback
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from collections import defaultdict
import re , logging


def home(request):
    return render(request, 'instructors_frontend/index.html')  # Original home page

def teaching_load(request):
    return render(request,'instructors_frontend/teaching_load.html')

def create_teaching_load(request):
    return render(request,'instructors_frontend/load_teacher.html')

def time_table(request):
    return render(request,'instructors_frontend/timetable.html')

# def room_schedule_view(request):
#     return render(request, 'scheduling_system/room_util.html')

def search_instructors(request):
    if request.method == "GET":
        query = request.GET.get('q', '').strip()  # Get the search query
        filter_type = request.GET.get('filter', 'ALL')  # Get the filter type (ALL, regular, cos)

        # Debugging: Print query and filter
        print(f"Search Query: {query}, Filter: {filter_type}")

        # Start with all instructors
        instructors = InstructorData.objects.all()

        # Apply filtering logic based on employment type
        if filter_type == 'REGULAR':
            instructors = instructors.filter(employment_type='REGULAR')
        elif filter_type == 'COS':
            instructors = instructors.filter(employment_type='COS')

        # Apply query if present
        if query:
            # Split the query into parts (split by spaces)
            name_parts = query.split()

            # Dynamically build the query filters based on the parts
            filter_query = Q()

            for part in name_parts:
                filter_query |= Q(first_name__icontains=part) | Q(middle_initial__icontains=part) | Q(last_name__icontains=part)

            instructors = instructors.filter(filter_query)

        # Debugging: Print the number of instructors fetched
        print(f"Found {instructors.count()} instructors matching the query.")

        # Prepare the response for the search (as JSON for AJAX)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Prepare the list of instructor details to return
            data = [
                {
                    'name': f"{instructor.first_name} {instructor.middle_initial or ''} {instructor.last_name}".strip(),
                    'instructor_id': instructor.instructor_id,
                    'employment_type': instructor.employment_type,
                    'qualified_course': instructor.qualified_course,
                }
                for instructor in instructors
            ]



            return JsonResponse({'results': data})

        # For non-AJAX request, render the instructor list template
        return render(request, 'instructors_frontend/teaching_load.html', {
            'instructors': instructors,
            'filter': filter_type,  # Pass the employment type filter to the template
            'query': query,  # Pass the search query to the template
        })


def instructor_details(request):
    # Get 'id' from query parameters
    instructor_id = request.GET.get('id')

    # Ensure the 'id' is provided and is a valid integer
    if not instructor_id:
        return JsonResponse({'error': 'instructor_id is required'}, status=400)

    try:
        # Convert the instructor_id to an integer (this will raise ValueError if it's not a valid number)
        instructor_id = int(instructor_id)

        # Fetch the instructor record
        instructor = InstructorData.objects.get(instructor_id=instructor_id)

        # Prepare the instructor details to return as JSON
        data = {
            'instructor_id': instructor.instructor_id,
            'name': f"{instructor.first_name} {instructor.middle_initial or ''} {instructor.last_name}".strip(),
            'employment_type': instructor.employment_type,
            'qualified_courses': instructor.qualified_course,
        }

        return JsonResponse(data)

    except ValueError:
        # If 'id' is not a valid integer, return an error
        return JsonResponse({'error': 'Invalid instructor_id format, must be an integer'}, status=400)
    except InstructorData.DoesNotExist:
        # If no instructor is found with the given ID
        return JsonResponse({'error': 'Instructor data not found'}, status=404)

# List instructor courses
def instructor_course_list(request):
    courses = InstructorCourse.objects.all()
    return render(request, 'teaching_load.html', {'courses': courses})

def search_programs(request):
    query = request.GET.get('q', '')
    if query:
        programs = Program.objects.filter(program_name__icontains=query)
    else:
        programs = Program.objects.all()

    program_list = [
        {
            'program_id': program.program_id,
            'program_name': program.program_name,
            'program_code': program.program_code,
        }
        for program in programs
    ]

    return JsonResponse({'programs': program_list})

def program_details(request):
    program_id = request.GET.get('program_id', None)
    if program_id:
        try:
            program = Program.objects.get(program_id=program_id)
            program_data = {
                'program_id': program.program_id,
                'program_name': program.program_name,
                'program_code': program.program_code,
            }
            return JsonResponse({'program': program_data})
        except Program.DoesNotExist:
            return JsonResponse({'error': 'Program not found'}, status=404)
    else:
        return JsonResponse({'error': 'Program ID not provided'}, status=400)

def search_courses(request):
    if request.method == "GET":
        query = request.GET.get('q', '').strip()  # Get the query from request
        courses = InstructorCourse.objects.all()  # Start with all courses

        if query:  # Apply filtering if query exists
            query_parts = query.split()  # Split the query into parts for flexibility
            filter_query = Q()

            # Build the filter dynamically to search in course_code and course_name
            for part in query_parts:
                filter_query |= Q(course_code__icontains=part) | Q(course_name__icontains=part)

            courses = courses.filter(filter_query)  # Apply the filters

        # Prepare the response for suggestions
        data = [
            {
                'course_code': course.course_code,
                'course_name': course.course_name,
                'course_id': course.course_id,
            }
            for course in courses
        ]
        return JsonResponse({'results': data})  # Return the suggestions as JSON

def course_details(request):
    course_id = request.GET.get('id')

    if not course_id:
        return JsonResponse({'error': 'Course ID is required.'}, status=400)

    try:
        course = InstructorCourse.objects.get(course_id=course_id)

        data = {
            'course_id': course.course_id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'credit_hours': course.credit_hours,
            'semester': course.semester,
        }
        return JsonResponse(data)

    except InstructorCourse.DoesNotExist:
        return JsonResponse({'error': 'Course not found.'}, status=404)

def room_utilization(request):
    return render(request, 'instructors_frontend/room_util.html')  # Update path to match your template location

def search_rooms(request):
    query = request.GET.get('q', '')  # Search query, default to empty string
    building_name = request.GET.get('building', '')  # Optionally filter by building name
    campus_name = request.GET.get('campus', '')  # Optionally filter by campus name

    rooms = Room.objects.all()  # Start with all rooms

    if query:  # Filter by room number if query is provided
        rooms = rooms.filter(room_number__icontains=query)

    if building_name:  # Filter by building name if provided
        rooms = rooms.filter(building__building_name__icontains=building_name)

    if campus_name:  # Filter by campus name if provided
        rooms = rooms.filter(campus__campus_name__icontains=campus_name)

    # Limit to 10 rooms and return relevant data
    rooms_data = [{"room_id": room.room_id, "room_number": room.room_number, "room_type": room.room_type} for room in rooms[:10]]

    return JsonResponse({'rooms': rooms_data})


def room_details(request):
    room_id = request.GET.get('room_id')

    try:
        room = Room.objects.get(room_id=room_id)
        data = {
            'room': {
                'room_number': room.room_number,
                'room_type': room.room_type,
                'building_name': room.building.building_name,
                'campus_name': room.campus.campus_name,
            }
        }
        return JsonResponse(data)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    
@csrf_exempt
def save_program_schedule(request):
    if request.method == "POST":
         # Extract skip_conflict_check parameter
        skip_conflict_check = request.POST.get('skip_conflict_check') == 'on'
        print(f"Skip Conflict Check: {skip_conflict_check}")  # Debug statement


        # Print all request data for debugging
        print(request.POST)

        # Extract and validate required fields
        instructor_name = request.POST.get('instructor_name')
        if not instructor_name:
            return JsonResponse({"error": "Instructor name is required."}, status=400)

        bachelor_degree = request.POST.get('bachelor_degree', "")
        master_degree = request.POST.get('master_degree', "")

        course_code = request.POST.get('course_code', "")
        course_name = request.POST.get('course_name', "")

        credit_hours = request.POST.get('credit_hours')
        if not credit_hours:
            return JsonResponse({"error": "Invalid whole number for credit hours."}, status=400)

        credit_unit = request.POST.get('credit_unit')
        if not credit_unit:
            return JsonResponse({"error": "Invalid whole number for credit unit."}, status=400)

        semester = request.POST.get('semester')
        program_name = request.POST.get('program_name')
        program_code = request.POST.get('program_code')

        # Handle room number and related fields
        room_number = request.POST.get('room_number', "").strip()
        room_type = request.POST.get('room_type', "").strip()
        building_name = request.POST.get('building_name')
        campus_name = request.POST.get('campus_name')

        year_level = request.POST.get('year_level')
        if not year_level:
            return JsonResponse({"error": "Year level is required."}, status=400)

        section = request.POST.get('section')
        shift = request.POST.get('shift')

        # Extracting all schedule entries
        schedule_days = []
        schedule_start_times = []
        schedule_end_times = []

        schedule_index = 0
        while True:
            day_key = f'schedules[{schedule_index}][day]'
            start_time_key = f'schedules[{schedule_index}][start_time]'
            end_time_key = f'schedules[{schedule_index}][end_time]'

            if day_key not in request.POST or start_time_key not in request.POST or end_time_key not in request.POST:
                break

            schedule_days.append(request.POST.get(day_key))
            schedule_start_times.append(request.POST.get(start_time_key))
            schedule_end_times.append(request.POST.get(end_time_key))

            schedule_index += 1

        if len(schedule_days) == 0:
            return JsonResponse({"error": "At least one schedule is required."}, status=400)

         # Validate and check for conflicts in schedules (only if skip_conflict_check is False)
        if not skip_conflict_check:
            print("Performing conflict check...")  # Debug statement
            for i in range(len(schedule_days)):
                day = schedule_days[i]
                start_time_str = schedule_start_times[i]
                end_time_str = schedule_end_times[i]
                pass
            else: 
                print("Skipping conflict check...")  # Debug statement



            # Validate day and time fields
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if day not in valid_days:
                return JsonResponse({"error": f"Invalid day '{day}'. Must be one of {', '.join(valid_days)}."}, status=400)

            if not start_time_str or not end_time_str:
                return JsonResponse({"error": "Both start time and end time are required."}, status=400)

            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError:
                return JsonResponse({"error": "Invalid time format. Use HH:MM."}, status=400)

            # Initialize the filters for conflict checking
            filters = Q(instructor_name=instructor_name)

            # Only include room in the filter if room_number is provided
            if room_number:
                filters |= Q(room_number=room_number)

            # Now check for conflicts based on schedules
            conflicts = Schedule.objects.filter(
                program_schedule__in=ProgramSchedule.objects.filter(filters),  # Only consider program schedules that match the filter
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            # Exclude schedules that have no room (skip them in conflict check)
            if room_number:  # If the new schedule has a room, exclude those without a room in the conflict check
                conflicts = conflicts.exclude(program_schedule__room_number='')

            # If any conflicts are found, handle them
            if conflicts.exists():
                conflict_details = conflicts.values(
                    'program_schedule__instructor_name', 
                    'program_schedule__course_code',
                    'program_schedule__room_number', 
                    'program_schedule__program_name',
                    'program_schedule__section',
                    'program_schedule__year_level',
                    'program_schedule__shift',
                    'day', 
                    'start_time', 
                    'end_time'
                )

                # Add custom conflict messages based on the type of conflict
                for conflict in conflict_details:
                    if conflict['program_schedule__instructor_name'] == instructor_name:
                        conflict['conflict_field'] = 'instructor_name'
                        conflict['conflict_message'] = "Instructor's schedule is already booked."
                    elif room_number and conflict['program_schedule__room_number'] == room_number:
                        conflict['conflict_field'] = 'room_number'
                        conflict['conflict_message'] = "Room schedule is already booked."
                    else:
                        conflict['conflict_field'] = 'schedule_time'
                        conflict['conflict_message'] = "Schedule time is already booked."

                return JsonResponse({"conflict": True, "details": list(conflict_details)}, status=200)

        # Save data to the ProgramSchedule model
        print("Saving data to the database...")  # Debug statement
        program_schedule = ProgramSchedule.objects.create(
            instructor_name=instructor_name,
            course_code=course_code,
            course_name=course_name,
            credit_hours=credit_hours,
            credit_unit=credit_unit,
            semester=semester,
            program_name=program_name,
            program_code=program_code,
            room_number=room_number,
            room_type=room_type,
            building_name=building_name,
            campus_name=campus_name,
            year_level=year_level,
            section=section,
            shift=shift,
            bachelor_degree=bachelor_degree,
            master_degree=master_degree
        )

        # Create the associated Schedule entries
        for i in range(len(schedule_days)):
            day = schedule_days[i]
            start_time_str = schedule_start_times[i]
            end_time_str = schedule_end_times[i]
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            Schedule.objects.create(
                program_schedule=program_schedule,
                day=day,
                start_time=start_time,
                end_time=end_time
            )

        return JsonResponse({"message": "Program schedule saved successfully!"})
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=400)

    
# View to fetch rooms and semesters
def fetch_room_and_semester_data(request):
    try:
        # Fetch available room names
        rooms = Room.objects.all().values('room_number')  # Adjust the field name if necessary

        # Fetch available semesters
        semesters = ProgramSchedule.objects.values_list('semester', flat=True).distinct()

        # Prepare the data to return
        data = {
            'rooms': list(rooms),
            'semesters': list(semesters)
        }

        return JsonResponse(data, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
def fetch_timetable_for_room(request):
    room_number = request.GET.get('room_number')
    semester = request.GET.get('semester')

    if not room_number or not semester:
        return JsonResponse({"error": "Room number and semester are required."}, status=400)

    # Fetch timetable data based on room_number and semester
    timetable = ProgramSchedule.objects.filter(
        room_number=room_number,
        semester=semester
    )

    # Prepare timetable data with proper time conversion
    timetable_data = []
    for entry in timetable:
        try:
            # Convert start_time and end_time from text to datetime.time objects
            start_time_str = entry.start_time  # '08:00'
            end_time_str = entry.end_time     # '09:00'
            
            # Convert the string time to datetime.time objects
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            timetable_data.append({
                'course_code': entry.course_code,
                'course_name': entry.course_name,
                'instructor_name': entry.instructor_name,
                'day': entry.day,
                'start_time': start_time.strftime('%H:%M'),  # Format the time for front-end
                'end_time': end_time.strftime('%H:%M'),
                'year_level': entry.year_level,
                'section': entry.section,
                'shift': entry.shift,
            })
        except Exception as e:
            print(f"Error processing timetable entry: {e}")

    return JsonResponse({'timetable': timetable_data})


# STORED DATA
def search_stored_data(request):
    # Log the request method and parameters for debugging
    print(f"Received request method: {request.method}")
    print(f"Request GET parameters: {request.GET}")

    if request.method == "GET":
        query = request.GET.get('q', '').strip()  # Get the search query
        filter_program = request.GET.get('filter', 'ALL')  # Get the filter type (ALL, program_name, etc.)

        # Log the received query and filter
        print(f"Received search query: '{query}'")
        print(f"Filter program: '{filter_program}'")

        # Fetch all records initially
        stored_data = ProgramSchedule.objects.all()

        # Apply program name filter if specified
        if filter_program != 'ALL':
            stored_data = stored_data.filter(program_name__iexact=filter_program)

        # Apply query if present
        if query:
            # Build the filter query dynamically for instructor name, course code, or course name
            filter_query = Q(instructor_name__icontains=query) | Q(course_code__icontains=query) | Q(course_name__icontains=query)
            stored_data = stored_data.filter(filter_query)

        # Log the filtered data count for debugging
        print(f"Filtered data count: {stored_data.count()}")

        # Respond with grouped data in JSON format for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Group data by instructor name
            instructor_data = defaultdict(list)
            for item in stored_data:
                instructor_data[item.instructor_name].append({
                    'course_code': item.course_code,
                    'course_name': item.course_name,
                    'program_name': item.program_name,
                    'degree_year_course': f"{item.year_level}, {item.program_name}",
                })

            # Format grouped data for the response
            results = []
            for instructor, courses in instructor_data.items():
                results.append({
                    'instructor_name': instructor,
                    'courses': courses
                })

            return JsonResponse({'results': results})

        # For non-AJAX requests, render a template (for debugging or fallback)
        return render(request, 'stored_data_frontend/teaching_load.html', {
            'stored_data': stored_data,
            'filter': filter_program,
            'query': query,
        })

def stored_data_details(request):
    # Get the 'name' parameter from the query string
    instructor_name = request.GET.get('name')

    if not instructor_name:
        return JsonResponse({'error': 'Instructor name is required'}, status=400)

    # Fetch the courses for the instructor by name
    try:
        courses = ProgramSchedule.objects.filter(instructor_name=instructor_name).values(
            'id', 'course_code', 'course_name'
        )

        # Fetch schedules for these courses
        course_schedule_data = []
        for course in courses:
            schedules = Schedule.objects.filter(program_schedule_id=course['id']).values(
                'day', 'start_time', 'end_time'
            )

            course_schedule_data.append({
                'course_code': course['course_code'],
                'course_name': course['course_name'],
                'schedule': [
                    {
                        'day': schedule['day'],
                        'start_time': schedule['start_time'].strftime('%H:%M'),
                        'end_time': schedule['end_time'].strftime('%H:%M')
                    }
                    for schedule in schedules
                ]
            })

        return JsonResponse({'courses': course_schedule_data})

    except ProgramSchedule.DoesNotExist:
        return JsonResponse({'error': 'Instructor not found'}, status=404)

    
    
#time table
# FOR PBT
def stored_time_details(request):
    instructor_name = request.GET.get('name')  # Use 'name' instead of 'id'

    if not instructor_name:
        return JsonResponse({'error': 'Instructor name is required'}, status=400)

    try:
        # Fetch instructor's courses and schedules by name
        courses = ProgramSchedule.objects.filter(instructor_name=instructor_name).values('id', 'course_code', 'course_name')
        if not courses.exists():
            return JsonResponse({'error': 'Instructor not found'}, status=404)

        # Fetch schedules for each course
        course_schedule_data = []
        for course in courses:
            schedules = Schedule.objects.filter(program_schedule_id=course['id']).values(
                'day', 'start_time', 'end_time'
            )
            course_schedule_data.append({
                'course_code': course['course_code'],
                'course_name': course['course_name'],
                'schedule': [
                    {
                        'day': schedule['day'],
                        'start_time': schedule['start_time'].strftime('%H:%M'),
                        'end_time': schedule['end_time'].strftime('%H:%M'),
                    }
                    for schedule in schedules
                ],
            })

        return JsonResponse({'courses': course_schedule_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
def get_instructor_schedule(request):
    instructor_name = request.GET.get('instructor_name', None)
    if not instructor_name:
        return JsonResponse({'error': 'No instructor name provided'}, status=400)

    try:
        # Fetch the related ProgramSchedule instances for the instructor
        program_schedules = ProgramSchedule.objects.filter(instructor_name=instructor_name)

        if not program_schedules.exists():
            return JsonResponse({'error': 'Instructor not found'}, status=404)

        # Fetch associated schedules and prefetch related ProgramSchedule data
        schedule_data = Schedule.objects.filter(program_schedule__in=program_schedules).select_related('program_schedule')

        # Format the schedule data
        courses = []
        for entry in schedule_data:
            # Access fields directly from entry (Schedule)
            # and related ProgramSchedule via entry.program_schedule
            courses.append({
                'course_code': entry.program_schedule.course_code,
                'course_name': entry.program_schedule.course_name,
                'room_number': entry.program_schedule.room_number or '',
                'section': entry.program_schedule.section or '',
                'program_code': entry.program_schedule.program_code or '',
                'year': entry.program_schedule.year_level or '',
                'level_shift': entry.program_schedule.shift or '',
                'day': entry.day.lower(),
                'start_time': entry.start_time.strftime("%H:%M"),
                'end_time': entry.end_time.strftime("%H:%M"),
            })

        return JsonResponse({'courses': courses})  # Return as a flat list

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_instructor_load(request):
    instructor_name = request.GET.get('instructor_name', None)
    if not instructor_name:
        return JsonResponse({'error': 'No instructor name provided'}, status=400)

    try:
        # Fetch ProgramSchedule entries for the instructor without total_students field.
        program_schedules = ProgramSchedule.objects.filter(instructor_name=instructor_name).values(
            'course_code',
            'course_name',
            'program_code',
            'section',
            'year_level',
            'shift',
        )

        if not program_schedules.exists():
            return JsonResponse({'error': 'No courses found for this instructor.'}, status=404)

        # Convert QuerySet to a list
        courses = list(program_schedules)
        
        # Optionally, add an empty total_students key for each course.
        for course in courses:
            course['total_students'] = ""

        return JsonResponse({'courses': courses})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def search_section(request):
    query = request.GET.get('q', '')
    sections = ProgramSchedule.objects.filter(section__icontains=query)
    data = [{"id": s.id, "name": s.section} for s in sections]
    return JsonResponse(data, safe=False)

def program_by_section(request):
    return render(request,'instructors_frontend/pbs.html')


def get_section_details(request):
    section_id = request.GET.get('section_id')
    section = get_object_or_404(ProgramSchedule, id=section_id)
    
    courses = [{
        "course_code": section.course_code,
        "course_name": section.course_name,
        "instructor": section.instructor_name,
        "room": section.room_number
    }]
    
    schedule = Schedule.objects.filter(program_schedule=section).values(
        "day", "start_time", "end_time"
    )
    
    return JsonResponse({
        "program_name": section.program_name,
        "year_level": section.year_level,
        "section": section.section,
        "courses": courses,
        "schedule": list(schedule)
    })

def filter_programs(request):
    program_codes = request.GET.get("program_codes", "").split(",")
    shift = request.GET.get("shift", "")
    year_levels = request.GET.get("year_levels", "").split(",")

    programs = ProgramSchedule.objects.all()

    if program_codes and program_codes[0]:
        programs = programs.filter(program_code__in=program_codes)
    if shift:
        programs = programs.filter(shift__iexact=shift)
    if year_levels and year_levels[0]:
        programs = programs.filter(year_level__in=year_levels)

    program_data = list(programs.values("program_code", "year_level", "section", "shift").distinct())

    return JsonResponse({"programs": program_data})


def get_program_list(request):
    """
    Fetches all unique program codes and names to populate the dropdown.
    """
    programs = ProgramSchedule.objects.values("program_code", "program_name").distinct()

    program_list = list(programs)  # Convert to list for JSON response

    return JsonResponse({"programs": program_list})


def search_program(request):
    program = request.GET.get('program', '').strip().upper()
    year_section = request.GET.get('year_section', '').strip()
    shift = request.GET.get('shift', '').strip()

    # Map user selection to actual programs in the database
    program_mapping = {
        "AUTO": ["BIT AUTO"],
        "COMPTECH": ["BIT CT"],
        "ENGINEER": ["BSCE", "BSME", "BSEE"],
        "EDUC": ["BEEd", "BTLED"],
        "BSHM": ["BSHM"]
    }

    if program == "ALL":
        query = ProgramSchedule.objects.all()
    elif program in program_mapping:
        query = ProgramSchedule.objects.filter(program_code__in=program_mapping[program])
    else:
        query = ProgramSchedule.objects.filter(
            Q(program_code__icontains=program) | Q(program_name__icontains=program)
        )

    # Extract year & section
    year_match = re.match(r'(\d+)', year_section)
    year_num = year_match.group(1) if year_match else ''
    section = year_section[len(year_num):].strip() if year_num else ''

    year_mapping = {'1': '1st Year', '2': '2nd Year', '3': '3rd Year', '4': '4th Year'}
    year_level = year_mapping.get(year_num, '')

    # Apply filters
    if year_level:
        query = query.filter(year_level=year_level)
    if shift:
        query = query.filter(shift__iexact=shift)

    results = list(query.values("program_code", "year_level", "section", "shift").distinct())

    # Add "No Section" if missing
    for item in results:
        if not item["section"]:
            item["section"] = "No Section"

    # Sorting function
    def sort_key(item):
        year_order = {"1st Year": 1, "2nd Year": 2, "3rd Year": 3, "4th Year": 4}
        section = item["section"] if item["section"] != "No Section" else "Z"  # Sort "No Section" last
        return (year_order.get(item["year_level"], 99), section)

    # Sort results
    results = sorted(results, key=sort_key)

    return JsonResponse({'results': results})

#  -----> PBS <------
 
def get_program_schedule(request):
    program_code = request.GET.get('program_code')
    year_level = request.GET.get('year_level')
    section = request.GET.get('section')
    shift = request.GET.get('shift')

    # Validate required parameters.
    if not (program_code and year_level and shift):
        return JsonResponse({'error': 'Missing required parameters.'}, status=400)
    
    try:
        # Use case‑insensitive filtering and handle empty section.
        qs = ProgramSchedule.objects.filter(
            program_code__iexact=program_code,
            year_level__iexact=year_level,
            shift__iexact=shift
        ).filter(
            Q(section__iexact=section) | Q(section__isnull=True) | Q(section__exact='')
        )
        
        courses = []
        # For each matching ProgramSchedule, loop through its related schedule entries.
        for ps in qs:
            schedule_entries = ps.schedules.all()
            for sch in schedule_entries:
                courses.append({
                    'course_code': ps.course_code,
                    'course_name': ps.course_name,
                    'program_code': ps.program_code,
                    'year_level': ps.year_level,
                    'section': ps.section,
                    'shift': ps.shift,
                    'instructor_name': ps.instructor_name,
                    'room_number': ps.room_number,
                    'day': sch.day,
                    'start_time': sch.start_time.strftime("%H:%M:%S"),
                    'end_time': sch.end_time.strftime("%H:%M:%S"),
                })
        # Instead of returning a 404, return an empty array if no courses are found.
        return JsonResponse({'courses': courses})
    
    except Exception as e:
        print("Error occurred:", str(e))
        print(traceback.format_exc())  # Prints full error details in console
        return JsonResponse({'error': str(e)}, status=500)
    
    
# ------- ROOM UTIL -----------
def get_room_suggestions(request):
    """API endpoint to get room suggestions for autocomplete based on user input"""
    query = request.GET.get('query', '').strip()
    
    # Only return filtered results based on what the user is typing
    if query:
        rooms = Room.objects.filter(
            Q(room_number__icontains=query) | 
            Q(room_type__icontains=query)
        ).values('room_number', 'room_type')[:10]  # Limit to 10 suggestions
    else:
        # If no query provided, return empty list instead of all rooms
        rooms = []
    
    return JsonResponse({'rooms': list(rooms)})

def get_room_schedule(request):
    """API endpoint to get schedules for a specific room"""
    room_number = request.GET.get('room_number', '').strip()
    
    if not room_number:
        return JsonResponse({'courses': []})
    
    # Find all program schedules that use this room
    program_schedules = ProgramSchedule.objects.filter(
        room_number__icontains=room_number
    )
    
    if not program_schedules.exists():
        return JsonResponse({'courses': []})
    
    # Get all schedules associated with these program schedules
    schedules = Schedule.objects.filter(program_schedule__in=program_schedules)
    
    courses = []
    
    # Combine program schedule and schedule information
    for schedule in schedules:
        ps = schedule.program_schedule
        
        course_info = {
            'instructor_name': ps.instructor_name,
            'course_code': ps.course_code,
            'course_name': ps.course_name,
            'program_code': ps.program_code,
            'room_number': ps.room_number,
            'year_level': ps.year_level,
            'section': ps.section,
            'shift': ps.shift,
            'day': schedule.day,
            'start_time': schedule.start_time.strftime('%H:%M:%S'),
            'end_time': schedule.end_time.strftime('%H:%M:%S')
        }
        
        courses.append(course_info)
    
    return JsonResponse({'courses': courses})