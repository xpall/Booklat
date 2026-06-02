from django.core.management.base import BaseCommand
from accounts.models import Role, Permission, RolePermission, User

ADMIN_PERMISSIONS = [
    "users.view", "users.create", "users.update", "users.archive",
    "users.password_reset",
    "books.view", "books.create", "books.update", "books.archive",
    "copies.view", "copies.create", "copies.update",
    "loans.create", "loans.return", "loans.view",
    "requests.process", "requests.view",
    "audit.view",
    "system.export_data", "system.import_data",
]

STAFF_PERMISSIONS = [
    "books.view", "books.create", "books.update", "books.archive",
    "copies.view", "copies.create", "copies.update",
    "loans.create", "loans.return",
    "requests.process", "requests.view",
]

MEMBER_PERMISSIONS = [
    "books.view",
    "loans.view",
    "requests.view",
]


class Command(BaseCommand):
    help = "Seed default roles, permissions, and an admin user"

    def handle(self, *args, **options):
        permissions = {}
        for codename in ADMIN_PERMISSIONS:
            name = codename.replace(".", " — ").title().replace("_", " ")
            perm, _ = Permission.objects.get_or_create(codename=codename, defaults={"name": name})
            permissions[codename] = perm

        admin_role, _ = Role.objects.get_or_create(
            name="Administrator",
            defaults={"description": "Full system access"},
        )
        for codename in ADMIN_PERMISSIONS:
            RolePermission.objects.get_or_create(role=admin_role, permission=permissions[codename])

        staff_role, _ = Role.objects.get_or_create(
            name="Staff",
            defaults={"description": "Library operational access"},
        )
        for codename in STAFF_PERMISSIONS:
            RolePermission.objects.get_or_create(role=staff_role, permission=permissions[codename])

        member_role, _ = Role.objects.get_or_create(
            name="Member",
            defaults={"description": "Library user"},
        )
        for codename in MEMBER_PERMISSIONS:
            RolePermission.objects.get_or_create(role=member_role, permission=permissions[codename])

        if not User.objects.filter(lrn="ADMIN").exists():
            admin = User(
                lrn="ADMIN",
                first_name="System",
                last_name="Administrator",
                role=admin_role,
                must_change_password=True,
            )
            admin.set_password("Booklat@Admin2026!")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: ADMIN / Booklat@Admin2026!"))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))