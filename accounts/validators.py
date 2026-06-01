from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumLengthValidator:
    def __init__(self, min_length=16):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters."),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return _("Password must be at least %(min_length)d characters.") % {"min_length": self.min_length}


class UppercaseValidator:
    def validate(self, password, user=None):
        if not any(c.isupper() for c in password):
            raise ValidationError(
                _("Password must contain at least 1 uppercase letter."),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _("Password must contain at least 1 uppercase letter.")


class LowercaseValidator:
    def validate(self, password, user=None):
        if not any(c.islower() for c in password):
            raise ValidationError(
                _("Password must contain at least 1 lowercase letter."),
                code="password_no_lower",
            )

    def get_help_text(self):
        return _("Password must contain at least 1 lowercase letter.")


class NumberValidator:
    def validate(self, password, user=None):
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("Password must contain at least 1 number."),
                code="password_no_number",
            )

    def get_help_text(self):
        return _("Password must contain at least 1 number.")


class SpecialCharacterValidator:
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"

    def validate(self, password, user=None):
        if not any(c in self.SPECIAL_CHARS for c in password):
            raise ValidationError(
                _("Password must contain at least 1 special character."),
                code="password_no_special",
            )

    def get_help_text(self):
        return _("Password must contain at least 1 special character.")