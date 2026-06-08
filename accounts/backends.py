from django.utils import timezone
from .models import User


class LRNAuthenticationBackend:
    def authenticate(self, request, lrn=None, password=None):
        now = timezone.now()
        try:
            user = User.objects.get(lrn=lrn)
        except User.DoesNotExist:
            User().check_password(password)
            return None
        if user.locked_until and user.locked_until > now:
            return None
        if user.check_password(password) and user.status == User.Status.ACTIVE:
            return user
        user.failed_login_attempts = user.failed_login_attempts + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timezone.timedelta(minutes=15)
            user.failed_login_attempts = 0
        user.save(update_fields=["failed_login_attempts", "locked_until"])
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None