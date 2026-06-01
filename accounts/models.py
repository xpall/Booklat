from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class Permission(models.Model):
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["codename"]

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, through="RolePermission")

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["role", "permission"]


class User(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"

    lrn = models.CharField(max_length=64, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "lrn"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.lrn})"

    @property
    def is_authenticated(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password

        return check_password(raw_password, self.password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm_codename):
        if self.role is None:
            return False
        return RolePermission.objects.filter(
            role=self.role, permission__codename=perm_codename
        ).exists()

    @property
    def id(self):
        return self.pk

    def get_session_auth_hash(self):
        import hashlib
        return hashlib.sha256(f"{self.pk}{self.password}".encode()).hexdigest()

    @property
    def is_admin(self):
        return self.role and self.role.name == "Administrator"

    @property
    def is_staff_user(self):
        return self.role and self.role.name == "Staff"

    @property
    def is_member(self):
        return self.role and self.role.name == "Member"