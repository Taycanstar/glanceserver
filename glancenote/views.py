from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from  openai import OpenAI  # Adjust import according to your project structure
import time
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from glancenote.text import send_verification_code
from glancenote.utils.csv import filter_csv_by_student, save_model_data_as_csv
from glancenote.utils.file import create_or_update_openai_assistant
from .models import Assistant, Student, TeacherProfile, User, Confirmation, ParentProfile, Course, Assignment, Log, Enrollment, AssignmentCompletion
import secrets
from decouple import config
from glancenote.utils.email import send_email_via_postmark
from django.contrib.auth.forms import UserCreationForm
from twilio.base.exceptions import TwilioRestException

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Set username to email
        if commit:
            user.save()
        return user


client = OpenAI()

@csrf_exempt
def openai_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_question = data.get('prompt')
        print(f"User question: {user_question}")
        # Create a thread using the assistantId
        thread = client.beta.threads.create()

        # Add user's question to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id, 
            role="user", 
            content=user_question
        )

        assistant = client.beta.assistants.create(
  name="Teacher Assistant",
  description="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt.",
  model="gpt-4-1106-preview",
  tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
  file_ids=[]
)

        # Create a run to process the message
        run = client.beta.threads.runs.create(
            thread_id=thread.id, 
            assistant_id=assistant.id  
        )

        # Wait for the run to complete
        run_status = None
        while run_status != "completed":
            run_status_response = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            run_status = run_status_response.status
            time.sleep(1)  # Wait before checking the status again

        # Retrieve messages after the run is completed
        messages = client.beta.threads.messages.list(thread.id)

        # Find the last message from the assistant
        last_message_for_run = next(
            (message for message in messages if message.run_id == run.id and message.role == "assistant"), 
            None
        )

        # Return the assistant's response
        if last_message_for_run:
            response_text = last_message_for_run.content[0].text.value  # Adjust according to the message structure
            print(f"AI Response: {response_text}")
            return JsonResponse({'response': response_text})
        else:
            print("Invalid request method")
            return JsonResponse({'error': 'No response received from the assistant.'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def parent_signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

       
        form = CustomUserCreationForm(data)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        if form.is_valid():
            user = form.save()

            # Create a ParentProfile instance
            user_profile = ParentProfile(
                user=user,
                email_verified=False,
                phone_verified=False,
            )
            user_profile.save()

            # Create a confirmation instance for email verification
            confirmationToken = secrets.token_hex(20)
            confirmation = Confirmation(
                email=email,
                confirmation_token=confirmationToken,
            )
            confirmation.save()

            # Prepare and send the verification email
            # Assuming you have these configurations and methods set up
            subject = "Verify Your Email"
            frontend_url = config('FRONTEND_URL')
            message = f"To continue setting up your Glance account, please click the following link to confirm your email: {frontend_url}/onboarding/info?token={confirmationToken}&email={email}"
            sender = config('EMAIL_SENDER')
            token = config('ONBOARDING_EMAIL_SERVER_TOKEN')
            send_email_via_postmark(subject, message, sender, [email], token)

            # Return a success response
            return JsonResponse({'message': 'Verification email sent successfully.'})

        else:
            return JsonResponse({'error': form.errors}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def parent_signup(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')
     # Use your custom form for user creation
    form = CustomUserCreationForm(data)
    
    confirmationToken = secrets.token_hex(20)

        # Check if the email already exists
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'User already exists'}, status=400)

    if form.is_valid():
        user = form.save()

        # Create a ParentProfile instance (assuming ParentProfile is the correct model here)
        user_profile = ParentProfile(
            user=user,
            email_verified=False,
            phone_verified=False,
        )
        user_profile.save()
    else:
        return JsonResponse({'error': form.errors}, status=400)

    # Create a confirmation instance for email verification
    confirmation = Confirmation(
        email=email,
        confirmation_token=confirmationToken,
    )
    confirmation.save()

    # Prepare and send the verification email
    subject = "Verify Your Email"
    frontend_url = config('FRONTEND_URL')
    message = f"To continue setting up your Glance account, please click the following link to confirm your email: {frontend_url}/onboarding/info?token={confirmationToken}&email={email}"
    
    sender = config('EMAIL_SENDER')
    token = config('ONBOARDING_EMAIL_SERVER_TOKEN')

    send_email_via_postmark(subject, message, sender, [email], token)

    # Return a success response
    return JsonResponse({'message': 'Verification email sent successfully.'})


@csrf_exempt
@require_http_methods(["PUT"])
def add_parent_info(request):
    try:
        # Load data from the request
        data = json.loads(request.body)
        email = data.get('email')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        student_id = data.get('studentId')
        phone_number = data.get('phoneNumber')

        # Find the user by email
        user = User.objects.get(email=email)

        # Retrieve or create the user's profile
        profile, created = ParentProfile.objects.get_or_create(user=user)

        # Update the profile with new data
        if first_name:
            profile.first_name = first_name
        if last_name:
            profile.last_name = last_name
        if phone_number:
            profile.phone_number = phone_number
        if student_id: 
            student = Student.objects.get(unique_id=student_id)
            profile.student = student  

        # Save the updated profile
        profile.save()

        if student_id:
            # Save data for each model as CSV
             if student_id:
            

            # Create or update the OpenAI assistant for the student
                try:
                    assistant_id = create_or_update_openai_assistant(student_id)
                    # Store the assistant in the database
                    parent_profile = ParentProfile.objects.get(user=user)
                    Assistant.objects.update_or_create(user=parent_profile, defaults={'assistant_id': assistant_id})
                except Exception as e:
                    return JsonResponse({'error': f'Failed to create/update assistant: {str(e)}'}, status=500)

           # Send verification SMS
        if phone_number:
            try:

                send_verification_code(phone_number)
            except TwilioRestException:
                # Handle Twilio exception for invalid phone number
                return JsonResponse({'error': 'Invalid phone number'}, status=400)

        return JsonResponse({'message': 'User profile updated successfully and SMS sent.'})

    except ObjectDoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

