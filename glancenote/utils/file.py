

import json
from glancenote.models import Assignment, AssignmentCompletion, Course, Enrollment, Institution, Student, Log
from glancenote.models import Assistant
from openai import OpenAI
import io
import csv
import os

client = OpenAI()

# Function to fetch log data for a student
def get_log_data_for_student(student):
    logs = Log.objects.filter(student=student).select_related('course')
    log_data = []
    for log in logs:
        log_data.append({
            'log_id': log.id,
            'date': log.date.strftime("%Y-%m-%d %H:%M"),
            'student_id': student.unique_id,
            'course_id': log.course.id if log.course else None,
            'course_name': log.course.name if log.course else None,
            'student_notes': log.student_notes,
            'professor_notes': log.professor_notes
        })
    return log_data

# Function to fetch assignment completion data for a student
def get_assignment_completion_data_for_student(student):
    completions = AssignmentCompletion.objects.filter(student=student).select_related('course', 'assignment')
    completion_data = []
    for completion in completions:
        completion_data.append({
            'completion_id': completion.id,
            'student_id': student.unique_id,
            'course_id': completion.course.id if completion.course else None,
            'course_name': completion.course.name if completion.course else None,
            'assignment_id': completion.assignment.id if completion.assignment else None,
            'assignment_name': completion.assignment.name if completion.assignment else None,
            'completion_date': completion.completion_date.strftime("%Y-%m-%d") if completion.completion_date else None,
            'grade': completion.grade,
            'completion_status': completion.completion_status
        })
    return completion_data

# Function to fetch course data
def get_course_data():
    courses = Course.objects.select_related('teacher').all()
    course_data = []
    for course in courses:
        teacher = course.teacher
        course_data.append({
            'course_id': course.id,
            'course_name': course.name,
            'course_code': course.code,
            'teacher_id': teacher.id if teacher else None,
            'teacher_name': teacher.user.get_full_name() if teacher else None,
            'institution_id': teacher.institution.id if teacher and teacher.institution else None
        })
    return course_data

# Function to fetch assignment data
def get_assignment_data():
    assignments = Assignment.objects.select_related('course').all()
    assignment_data = []
    for assignment in assignments:
        assignment_data.append({
            'assignment_id': assignment.id,
            'assignment_name': assignment.name,
            'due_date': assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else None,
            'course_id': assignment.course.id if assignment.course else None,
            'course_name': assignment.course.name if assignment.course else None
        })
    return assignment_data

# Function to fetch enrollment data for a student
def get_enrollment_data(student):
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    enrollment_data = []
    for enrollment in enrollments:
        enrollment_data.append({
            'student_id': student.unique_id,
            'course_id': enrollment.course.id if enrollment.course else None,
            'course_name': enrollment.course.name if enrollment.course else None,
            'enrollment_date': enrollment.enrollment_date.strftime("%Y-%m-%d") if enrollment.enrollment_date else None
        })
    return enrollment_data

# Function to fetch specific student data
def get_specific_student_data(student_unique_id):
    try:
        student = Student.objects.get(unique_id=student_unique_id)
        return {
            'student_id': student.unique_id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'phone_number': student.phone_number,
            'institution_id': student.institution.id if student.institution else None,
            'institution_name': student.institution.name if student.institution else None
        }
    except Student.DoesNotExist:
        return None

# Function to fetch institution data
def get_institution_data():
    institutions = Institution.objects.all()
    institution_data = []
    for institution in institutions:
        institution_data.append({
            'institution_id': institution.id,
            'name': institution.name,
            'address': institution.address,
            'website': institution.website,
            'domains': institution.domains
        })
    return institution_data

# Function to get formatted data for a student
def get_formatted_data(student_id):
    student = Student.objects.filter(unique_id=student_id).first()
    if not student:
        print("Student not found for unique_id:", student_id)
        return {}  # Handle case where student doesn't exist

    student_data = get_specific_student_data(student_id)
    course_data = get_course_data()
    assignment_data = get_assignment_data()
    completion_data = get_assignment_completion_data_for_student(student)
    log_data = get_log_data_for_student(student)
    enrollment_data = get_enrollment_data(student)
    institution_data = get_institution_data()

    formatted_data = {
        'student': [student_data] if student_data else [],
        'courses': course_data,
        'assignments': assignment_data,
        'completions': completion_data,
        'logs': log_data,
        'enrollments': enrollment_data,
        'institutions': institution_data
    }

    return formatted_data

def convert_data_to_csv_string(data):
    if not data:  # Check if data is empty
        return None

    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(data[0].keys())  # Column headers

    for row in data:
        writer.writerow(row.values())

    return output.getvalue().strip()


def save_data_as_csv_file(data, filename):
    csv_data = convert_data_to_csv_string(data)
    if csv_data is not None:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_data)
        print(f"File saved: {filename}")
        return filename
    else:
        print(f"No data for {filename}. File not created.")
        return None



def create_csv_files_for_openai_assistant(student_id):
    try:
        student_data = get_formatted_data(student_id)
        file_paths = []

        for category in ['student', 'courses', 'enrollments', 'assignments', 'institutions', 'logs', 'completions']:
            if student_data.get(category):
                filename = f"{category}.csv"
                file_path = save_data_as_csv_file(student_data[category], filename)
                if file_path:
                    file_paths.append(file_path)

        return file_paths
    except Exception as e:
        print(f"Error in creating CSV files: {e}")
        return []

def upload_file(client, filename, purpose):
    with open(filename, "rb") as file:
        contents = file.read()
        if not contents:
            print(f"Warning: {filename} is empty.")
        return client.files.create(file=contents, purpose=purpose)


def upload_data_as_file(file_path, purpose='assistants', client=client):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print(f"File {file_path} is empty or does not exist.")
        return None

    try:
        with open(file_path, 'rb') as file_to_upload:
            response = client.files.create(file=file_to_upload, purpose=purpose)
            return response.id  # Extract the file ID from the response
    except Exception as e:
        print(f"Error during file upload: {e}")

    return None



def create_or_update_openai_assistant(student_id):
    file_paths = create_csv_files_for_openai_assistant(student_id)
    file_ids = []

    for file_path in file_paths:
        if file_path:  # Check if file_path is not None
            file_id = upload_data_as_file(file_path, 'assistants')
            if file_id:
                file_ids.append(file_id)

    if not file_ids:
        print("Error: No files were uploaded successfully.")
        return None

    assistant = client.beta.assistants.create(
        name="Teacher Assistant",
        instructions="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt.",
        model="gpt-4",
        tools=[{"type": "code_interpreter"}],
        file_ids=file_ids
    )


    return assistant.id



def create(student_id):
    # Generate the CSV files for the given student
    file_paths = create_csv_files_for_openai_assistant(student_id)
    if not file_paths:
        print("Failed to create CSV files")
        return None

    # Upload each file and collect their IDs
    file_ids = []
    for file_path in file_paths:
        try:
            uploaded_file = upload_file(client, file_path, 'assistants')
            if uploaded_file:
                file_ids.append(uploaded_file.id)
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

    # Check if any files were successfully uploaded
    if not file_ids:
        print("No files were uploaded successfully.")
        return None

    # Create the assistant with the uploaded files
    try:
        assistant = client.beta.assistants.create(
            name="Teacher Assistant",
            instructions="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt.",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
            file_ids=file_ids
        )
        print(assistant)
    except Exception as e:
        print(f"Error creating assistant: {e}")


