from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid
from random import randint



class Institution(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField( blank=True)
    website = models.CharField(max_length=200, blank=True)
    domains = models.JSONField(default=list, blank=True)


    def __str__(self):
        return self.name
    

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='teacher_photos/', null=True, blank=True)
    phone_verified = models.BooleanField(default=False, blank=True)
    email_verified = models.BooleanField(default=False, blank=True)
    courses = models.ManyToManyField('Course', blank=True, related_name='teachers')
    registration_tokens = models.JSONField(default=list,  blank=True)
    phone_number = models.CharField(max_length=20, blank=True, )
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='teachers', null=True)

class Student(models.Model):
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20,  blank=True)
    mentors = models.ManyToManyField(TeacherProfile, related_name='mentored_students', blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='students', null=True)
    unique_id = models.IntegerField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            # Generate a unique 7-digit number
            self.unique_id = self.generate_unique_id()
        super(Student, self).save(*args, **kwargs)

    @staticmethod
    def generate_unique_id():
        range_start = 10**(7-1)
        range_end = (10**7)-1
        generated_id = randint(range_start, range_end)
        while Student.objects.filter(unique_id=generated_id).exists():
            generated_id = randint(range_start, range_end)
        return generated_id

    def __str__(self):
        return self.first_name + " " + self.last_name
    
class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, null=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='taught_courses',  null=True,  blank=True)

    class Meta:
        verbose_name_plural = "Courses"


    def __str__(self):
        return self.name

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    due_date = models.DateTimeField( blank=True)

    def __str__(self):
        return self.name

class AssignmentCompletion(models.Model):
    # Define fields like student_id, name, etc.
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True)
    completion_date = models.DateTimeField( blank=True)
    completion_status = models.BooleanField(default=False)
    grade = models.CharField(max_length=20, blank=True)
    

class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    enrollment_date = models.DateTimeField( blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Enrollments"

class Log(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField()
    student_notes = models.CharField(max_length=1000, blank=True)
    professor_notes = models.CharField(max_length=1000, blank=True)


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    birthday = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    registration_tokens = models.JSONField(default=list)
    subscription = models.CharField(max_length=100, blank=True)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.email



class Confirmation(models.Model):
    email = models.EmailField()
    hashed_password = models.CharField(max_length=255)  # Adjust the max_length as appropriate
    confirmation_token = models.CharField(max_length=255)  # Adjust the max_length as appropriate
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email


class Assistant(models.Model):
    user = models.OneToOneField(ParentProfile, on_delete=models.CASCADE)
    files = models.JSONField(default=list)
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"

    
