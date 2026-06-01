from .models import User


class LRNAuthenticationBackend:
    def authenticate(self, request, lrn=None, password=None):
        try:
            user = User.objects.get(lrn=lrn)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and user.status == User.Status.ACTIVE:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None