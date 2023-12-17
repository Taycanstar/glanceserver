from django.contrib import admin
from .models import Institution, Student, Course, Assignment, AssignmentCompletion, Enrollment, Log, ParentProfile,Confirmation, TeacherProfile, Assistant

class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'phone_number', 'institution')

admin.site.register(Confirmation)
admin.site.register(ParentProfile)
admin.site.register(Student, StudentAdmin)
admin.site.register(Enrollment)
admin.site.register(Course)
admin.site.register(Log)
admin.site.register(Assignment)
admin.site.register(AssignmentCompletion)
admin.site.register(TeacherProfile)
admin.site.register(Institution)
admin.site.register(Assistant)



