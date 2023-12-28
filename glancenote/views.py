import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from  openai import OpenAI  # Adjust import according to your project structure
import time
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from glancenote.text import send_verification_code,  verify_number
from glancenote.utils.file import create_or_update_openai_assistant
from .models import Assistant, Student, TeacherProfile, User, Confirmation, ParentProfile, Course, Assignment, Log, Enrollment, AssignmentCompletion, Institution
import secrets
from decouple import config
from glancenote.utils.email import send_email_via_postmark
from django.contrib.auth.forms import UserCreationForm
from twilio.base.exceptions import TwilioRestException
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from datetime import datetime



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
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            user_question = data.get('prompt')
            user_email = data.get('email')  # User's email

            # Retrieve the user and their parent profile
            user = User.objects.get(email=user_email)
            parent_profile = ParentProfile.objects.get(user=user)
            # assistant_id = parent_profile.assistant.assistant_id  
            assistant_id = "asst_CWCg6YI4UiRrj3lA9AGc90qZ"  

            if not assistant_id:
                return JsonResponse({'error': 'Assistant ID not found.'}, status=404)

            # Check if there is an existing thread_id, otherwise create a new thread
            if not parent_profile.thread_id:
                thread = client.beta.threads.create()
                parent_profile.thread_id = thread.id
                parent_profile.save()
            thread_id = parent_profile.thread_id

            # Add user's question to the thread
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_question
            )

            # Create a run to process the message with the specific assistant
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )

            # Wait for the run to complete
            run_status = None
            while run_status != "completed":
                run_status_response = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                run_status = run_status_response.status
                time.sleep(1)  # Wait before checking the status again

            # Retrieve messages after the run is completed
            messages = client.beta.threads.messages.list(thread_id)

            # Find the last message from the assistant
            last_message_for_run = next(
                (message for message in messages if message.run_id == run.id and message.role == "assistant"),
                None
            )

            # Return the assistant's response
            if last_message_for_run:
                response_text = last_message_for_run.content[0].text.value
                return JsonResponse({'response': response_text})
            else:
                return JsonResponse({'error': 'No response received from the assistant.'})

        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)

    except ParentProfile.DoesNotExist:
        return JsonResponse({'error': 'ParentProfile not found'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def teacher_signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        institution_name = data.get('institution')  # Name of the institution

        # Dictionary mapping dropdown options to domains
        domain_mapping = {
            "Gmail": "@gmail.com",
            "Eckerd College": "@eckerd.edu",
        }

        # Check if the selected institution is in the dictionary and validate the domain
        if institution_name in domain_mapping and email.endswith(domain_mapping[institution_name]):
            form = CustomUserCreationForm(data)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'User already exists'}, status=400)

            if form.is_valid():
                user = form.save()

                # Retrieve the Institution instance
                try:
                    institution = Institution.objects.get(name=institution_name)
                except Institution.DoesNotExist:
                    return JsonResponse({'error': 'Institution not found'}, status=400)

                # Create a TeacherProfile instance with the Institution instance
                user_profile = TeacherProfile(
                    user=user,
                    email_verified=False,
                    phone_verified=False,
                    institution=institution  # Assign the Institution instance
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
                subject = "Verify Your Email"
                frontend_url = config('FRONTEND_URL')
                message = f"To continue setting up your account, please click the following link to confirm your email: {frontend_url}/onboarding/info-teacher?token={confirmationToken}&email={email}"
                sender = config('EMAIL_SENDER')
                token = config('ONBOARDING_EMAIL_SERVER_TOKEN')
                send_email_via_postmark(subject, message, sender, [email], token)

                return JsonResponse({'message': 'Verification email sent successfully.'})

            else:
                return JsonResponse({'error': form.errors}, status=400)
        else:
            return JsonResponse({'error': 'Unable to verify institution'}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


  
@csrf_exempt
@require_http_methods(["PUT"])
def add_teacher_info(request):
    try:
        # Load data from the request
        data = json.loads(request.body)
        email = data.get('email')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        birthday = data.get('birthday')
        gender = data.get('gender')
        phone_number = data.get('phoneNumber')

        # Find the user by email
        user = User.objects.get(email=email)

        # Retrieve or create the user's profile
        profile, created = TeacherProfile.objects.get_or_create(user=user)

        # Update the profile with new data
        if first_name:
            profile.first_name = first_name
        if last_name:
            profile.last_name = last_name
        if phone_number:
            profile.phone_number = phone_number
        if birthday:
            try:
                # Convert from "MM/DD/YYYY" to "YYYY-MM-DD"
                formatted_birthday = datetime.strptime(birthday, "%m/%d/%Y").date()
                profile.birthday = formatted_birthday
            except ValueError as e:
                return JsonResponse({'error': f'Invalid birthday format: {str(e)}'}, status=400)
        if gender:
            profile.birthday = gender

        # Save the updated profile
        profile.save()

        if phone_number:
            try:
                send_verification_code(phone_number)
            except TwilioRestException as e:
                print(f"TwilioRestException: {e}")
                return JsonResponse({'error': 'Invalid phone number'}, status=400)

        return JsonResponse({'message': 'User profile updated successfully and SMS sent.'})

    except ObjectDoesNotExist as e:
        print(f"ObjectDoesNotExist: {e}")
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"General Exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def confirm_teacher_email(request):
    try:
        data = json.loads(request.body)
        confirmation_token = data.get('confirmationToken')
        email = data.get('email')

        # Retrieve the confirmation instance
        try:
            confirmation = Confirmation.objects.get(confirmation_token=confirmation_token)
        except Confirmation.DoesNotExist:
            return JsonResponse({'message': 'Confirmation token not found'}, status=404)

        # Check if email matches
        if confirmation.email != email:
            return JsonResponse({'message': 'Invalid confirmation token or email'}, status=401)

        # Find or create the user
        user, created = User.objects.get_or_create(email=email)

        # Update or create the user profile
        profile, created = TeacherProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save()

        # Delete the confirmation instance
        confirmation.delete()

        return JsonResponse({'message': 'User confirmed and email verified'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:

        traceback.print_exc()  # This will print the full traceback to your console or logs
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def resend_teacher_email(request):
    data = json.loads(request.body)
    email = data.get('email')

    # Retrieve the user and their associated UserProfile
    try:
        user = User.objects.get(email=email)
        user_profile = TeacherProfile.objects.get(user=user)
    except (User.DoesNotExist, ParentProfile.DoesNotExist):
        return JsonResponse({'error': 'User not found.'}, status=404)

    # Check if the user's email is already verified
    if user_profile.email_verified:
        return JsonResponse({'message': 'Email is already verified.'})

    # Retrieve the existing confirmation token
    try:
        confirmation = Confirmation.objects.get(email=email)
        confirmationToken = confirmation.confirmation_token
    except Confirmation.DoesNotExist:
        return JsonResponse({'error': 'Confirmation token not found.'}, status=404)

    # Prepare and resend the verification email
    subject = "Verify Your Email"
    frontend_url = config('FRONTEND_URL')
    message = f"To continue setting up your Glancenote account, please click the following link to confirm your email: {frontend_url}/onboarding/info?token={confirmationToken}&email={email}"
    
    sender = config('EMAIL_SENDER')
    token = config('ONBOARDING_EMAIL_SERVER_TOKEN')

    send_email_via_postmark(subject, message, sender, [email], token)

    # Return a success response
    return JsonResponse({'message': 'Verification email resent successfully.'})



@csrf_exempt
@require_http_methods(["POST"])
def resend_teacher_code(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        # Retrieve the user's profile
      
        try:
            user = User.objects.get(email=email)
            user_profile = TeacherProfile.objects.get(user=user)
        except ParentProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile not found'}, status=404)

        # Resend the OTP code
        phone_number = user_profile.phone_number
        if phone_number:
            send_verification_code(phone_number)  # Replace with your OTP sending logic
            return JsonResponse({'message': 'OTP code resent successfully'})
        else:
            return JsonResponse({'error': 'Phone number not found'}, status=404)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
def confirm_teacher_ph(request):
    try:
        data = json.loads(request.body)
        phone_number = data.get('phoneNumber')
        email = data.get('email')
        otp_code = data.get('code')

        verification_check = verify_number(phone_number, otp_code)

        try:
            user = User.objects.get(email=email)
            user_profile = TeacherProfile.objects.get(user=user)
        except ParentProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile not found'}, status=404)
        
        if verification_check.status == "approved":
            user_profile.phone_verified = True
            user_profile.save()
            return JsonResponse({'message': 'Phone number verified.'})
        else:
            return JsonResponse({'message': 'Invalid verification code.'}, status=400)

    except Exception as e:
        traceback.print_exc()
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
    message = f"To continue setting up your Glancenote account, please click the following link to confirm your email: {frontend_url}/onboarding/info?token={confirmationToken}&email={email}"
    
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
            try:
                assistant_id = create_or_update_openai_assistant(student_id)
                parent_profile = ParentProfile.objects.get(user=user)
                Assistant.objects.update_or_create(user=parent_profile, defaults={'assistant_id': assistant_id})
            except Exception as e:
                print(f"Failed to create/update assistant: {e}")
                return JsonResponse({'error': f'Failed to create/update assistant: {str(e)}'}, status=500)

        if phone_number:
            try:
                send_verification_code(phone_number)
            except TwilioRestException as e:
                print(f"TwilioRestException: {e}")
                return JsonResponse({'error': 'Invalid phone number'}, status=400)

        return JsonResponse({'message': 'User profile updated successfully and SMS sent.'})

    except ObjectDoesNotExist as e:
        print(f"ObjectDoesNotExist: {e}")
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"General Exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def confirm_parent_email(request):
    try:
        data = json.loads(request.body)
        confirmation_token = data.get('confirmationToken')
        email = data.get('email')

        # Retrieve the confirmation instance
        try:
            confirmation = Confirmation.objects.get(confirmation_token=confirmation_token)
        except Confirmation.DoesNotExist:
            return JsonResponse({'message': 'Confirmation token not found'}, status=404)

        # Check if email matches
        if confirmation.email != email:
            return JsonResponse({'message': 'Invalid confirmation token or email'}, status=401)

        # Find or create the user
        user, created = User.objects.get_or_create(email=email)

        # Update or create the user profile
        profile, created = ParentProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save()

        # Delete the confirmation instance
        confirmation.delete()

        return JsonResponse({'message': 'User confirmed and email verified'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:

        traceback.print_exc()  # This will print the full traceback to your console or logs
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def resend_parent_email(request):
    data = json.loads(request.body)
    email = data.get('email')

    # Retrieve the user and their associated UserProfile
    try:
        user = User.objects.get(email=email)
        user_profile = ParentProfile.objects.get(user=user)
    except (User.DoesNotExist, ParentProfile.DoesNotExist):
        return JsonResponse({'error': 'User not found.'}, status=404)

    # Check if the user's email is already verified
    if user_profile.email_verified:
        return JsonResponse({'message': 'Email is already verified.'})

    # Retrieve the existing confirmation token
    try:
        confirmation = Confirmation.objects.get(email=email)
        confirmationToken = confirmation.confirmation_token
    except Confirmation.DoesNotExist:
        return JsonResponse({'error': 'Confirmation token not found.'}, status=404)

    # Prepare and resend the verification email
    subject = "Verify Your Email"
    frontend_url = config('FRONTEND_URL')
    message = f"To continue setting up your Glancenote account, please click the following link to confirm your email: {frontend_url}/onboarding/info?token={confirmationToken}&email={email}"
    
    sender = config('EMAIL_SENDER')
    token = config('ONBOARDING_EMAIL_SERVER_TOKEN')

    send_email_via_postmark(subject, message, sender, [email], token)

    # Return a success response
    return JsonResponse({'message': 'Verification email resent successfully.'})



@csrf_exempt
@require_http_methods(["POST"])
def resend_parent_code(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        # Retrieve the user's profile
      
        try:
            user = User.objects.get(email=email)
            user_profile = ParentProfile.objects.get(user=user)
        except ParentProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile not found'}, status=404)

        # Resend the OTP code
        phone_number = user_profile.phone_number
        if phone_number:
            send_verification_code(phone_number)  # Replace with your OTP sending logic
            return JsonResponse({'message': 'OTP code resent successfully'})
        else:
            return JsonResponse({'error': 'Phone number not found'}, status=404)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
def confirm_parent_ph(request):
    try:
        data = json.loads(request.body)
        phone_number = data.get('phoneNumber')
        email = data.get('email')
        otp_code = data.get('code')

        verification_check = verify_number(phone_number, otp_code)

        try:
            user = User.objects.get(email=email)
            user_profile = ParentProfile.objects.get(user=user)
        except ParentProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile not found'}, status=404)
        
        if verification_check.status == "approved":
            user_profile.phone_verified = True
            user_profile.save()
            return JsonResponse({'message': 'Phone number verified.'})
        else:
            return JsonResponse({'message': 'Invalid verification code.'}, status=400)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
def login_without_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        user = authenticate(email=email)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            user_type = None
            if ParentProfile.objects.filter(user=user).exists():
                user_type = 'Parent'
            elif TeacherProfile.objects.filter(user=user).exists():
                user_type = 'Teacher'

            return JsonResponse({
                'message': 'Login successful',
                'token': token.key,
                "user": email,
                'userType': user_type
            })
        else:
            return JsonResponse({'error': 'Authentication failed'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            user_data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }

             # Determine if the user is a Parent or Teacher
            user_type = None
            if ParentProfile.objects.filter(user=user).exists():
                user_type = 'Parent'
            elif TeacherProfile.objects.filter(user=user).exists():
                user_type = 'Teacher'

            # Check if the user has a ParentProfile
            try:
                parent_profile = ParentProfile.objects.get(user=user)
                profile_data = {
                    'gender': parent_profile.gender,
                    'phone_number': parent_profile.phone_number,
                    'birthday': parent_profile.birthday,
                    'photo': parent_profile.photo.url if parent_profile.photo else None,
                    'subscription': parent_profile.subscription,
                    'phone_verified': parent_profile.phone_verified,
                    'email_verified': parent_profile.email_verified,
                    'student': parent_profile.student.id if parent_profile.student else None
                }
                user_data.update(profile_data)
                user_data['profile_type'] = 'Parent'
            except ParentProfile.DoesNotExist:
                pass

            # Check if the user has a TeacherProfile
            try:
                teacher_profile = TeacherProfile.objects.get(user=user)
                profile_data = {
                    'photo': teacher_profile.photo.url if teacher_profile.photo else None,
                    'phone_verified': teacher_profile.phone_verified,
                    'email_verified': teacher_profile.email_verified,
                    'phone_number': teacher_profile.phone_number,
                    'birthday': teacher_profile.birthday,
                    'gender': teacher_profile.gender,
                    'institution': teacher_profile.institution.id if teacher_profile.institution else None,
                    'courses': list(teacher_profile.courses.values_list('id', flat=True))
                }
                user_data.update(profile_data)
                user_data['profile_type'] = 'Teacher'
            except TeacherProfile.DoesNotExist:
                pass

            return JsonResponse({
                'message': 'Login successful',
                'user': email,
                'token': token.key,
                'userType': user_type
            })

        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def initialize_thread(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        user = User.objects.get(email=email)
        parent_profile = ParentProfile.objects.get(user=user)

        if not parent_profile.thread_id:
            # If there is no thread_id, create a new thread
            thread = client.beta.threads.create()
            parent_profile.thread_id = thread.id
            parent_profile.save()

        return JsonResponse({'thread_id': parent_profile.thread_id})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except ParentProfile.DoesNotExist:
        return JsonResponse({'error': 'ParentProfile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)