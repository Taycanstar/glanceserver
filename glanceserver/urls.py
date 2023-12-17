
from django.contrib import admin
from django.urls import path
from glancenote.views import openai_chat, parent_signup, add_parent_info

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/openai_chat/', openai_chat, name='openai_chat'),
    path('api/parent_signup/', parent_signup, name='parent_signup'),
    path('api/add_parent_info/', add_parent_info, name='add_parent_info'),
    
]
