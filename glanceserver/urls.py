
from django.contrib import admin
from django.urls import path
from glancenote.views import openai_chat

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/openai_chat/', openai_chat, name='openai_chat'),
    
]
