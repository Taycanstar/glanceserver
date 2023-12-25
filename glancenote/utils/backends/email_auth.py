from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class EmailOnlyAuthenticationBackend(BaseBackend):
    def authenticate(self, request, email=None):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            # You can add additional checks here if needed
            return user
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
