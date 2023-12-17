

import json
from glancenote.models import Assignment, AssignmentCompletion, Course, Enrollment, Institution, Student, Log
from glancenote.models import Assistant
from openai import OpenAI
import io
import csv
import os

client = OpenAI()

def get_student_data_for_openai(student_unique_id):
    # Fetch the student by unique_id instead of id
    student = Student.objects.filter(unique_id=student_unique_id).first()
    if not student:
        return {}  # Or handle the case where the student doesn't exist

    # Fetch relevant data for the student
    student_data = Student.objects.filter(unique_id=student_unique_id).values()
    course_data = Course.objects.values()
    enrollment_data = Enrollment.objects.filter(student=student).values()
    assignment_data = Assignment.objects.values()
    institution_data = Institution.objects.values()
    log_data = Log.objects.filter(student=student).values()
    assignment_completion_data = AssignmentCompletion.objects.filter(student=student)

    # Process and format data as needed for OpenAI
    formatted_data = {
        'student': list(student_data),  # Assuming you want to keep the structure consistent
        'courses': list(course_data),
        'enrollments': list(enrollment_data),
        'assignments': list(assignment_data),
        'institutions': list(institution_data),
        'logs': list(log_data),
        'completions': list(assignment_completion_data)
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
    student_data = get_student_data_for_openai(student_id)
    file_paths = []

    for category in ['student', 'courses', 'enrollments', 'assignments', 'institutions', 'logs', 'completions']:
        filename = f"{category}.csv"
        file_path = save_data_as_csv_file(student_data[category], filename)
        if file_path:
            file_paths.append(file_path)

    return file_paths



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
        description="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt.",
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
        file_ids=file_ids
    )

    return assistant.id




def create():
    file_paths = ["assignments.csv", "courses.csv", "enrollments.csv"]
    file_ids = []

    for file_path in file_paths:
        try:
            uploaded_file = upload_file(client, file_path, 'assistants')
            if uploaded_file:
                file_ids.append(uploaded_file.id)
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

    if not file_ids:
        print("No files were uploaded successfully.")
        return None

    assistant = client.beta.assistants.create(
        name="Teacher Assistant",
        description="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt.",
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
        file_ids=file_ids
    )

    print(assistant)




