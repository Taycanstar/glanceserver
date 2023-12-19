
from django.contrib import admin
from django.urls import path
from glancenote.views import confirm_parent_email, confirm_parent_ph, openai_chat, parent_signup, add_parent_info, resend_parent_code, resend_parent_email

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/openai-chat/', openai_chat, name='openai_chat'),
    path('api/parent-signup/', parent_signup, name='parent_signup'),
    path('api/add-parent-info/', add_parent_info, name='add_parent_info'),
    path('api/confirm-parent-email/', confirm_parent_email, name='confirm_parent_email'),
    path('api/resend-parent-email/', resend_parent_email, name='resend_parent_email'),
    path('api/resend-parent-code/', resend_parent_code, name='resend_parent_code'),
    path('api/confirm-parent-ph/', confirm_parent_ph, name='confirm_parent_ph'),
    
    
]
