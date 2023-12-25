
from django.contrib import admin
from django.urls import path
from glancenote.views import confirm_parent_email, confirm_parent_ph, login, login_without_password, openai_chat, parent_signup, add_parent_info, resend_parent_code, resend_parent_email, initialize_thread, resend_teacher_code, confirm_teacher_email, confirm_teacher_ph, teacher_signup, add_teacher_info, resend_teacher_email, resend_teacher_code

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/openai-chat/', openai_chat, name='openai_chat'),
    path('api/parent-signup/', parent_signup, name='parent_signup'),
    path('api/add-parent-info/', add_parent_info, name='add_parent_info'),
    path('api/confirm-parent-email/', confirm_parent_email, name='confirm_parent_email'),
    path('api/resend-parent-email/', resend_parent_email, name='resend_parent_email'),
    path('api/resend-parent-code/', resend_parent_code, name='resend_parent_code'),
    path('api/confirm-parent-ph/', confirm_parent_ph, name='confirm_parent_ph'),
    path('api/login/', login, name='login'),
    path('api/login-without-password/', login_without_password, name='login-without-password'),
    path('api/initialize-thread/', initialize_thread, name='initialize_thread'),
    path('api/teacher-signup/', teacher_signup, name='teacher_signup'),
    path('api/add-teacher-info/', add_teacher_info, name='add_teacher_info'),
    path('api/confirm-teacher-email/', confirm_teacher_email, name='confirm_teacher_email'),
    path('api/resend-teacher-email/', resend_teacher_email, name='resend_teacher_email'),
    path('api/resend-teacher-code/', resend_teacher_code, name='resend_teacher_code'),
    path('api/confirm-teacher-ph/', confirm_teacher_ph, name='confirm_teacher_ph'),
    path('api/resend-teacher-code/', resend_teacher_code, name='resend_teacher_code'),

    
    
]
