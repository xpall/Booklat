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
    "categories.manage",
    "freedom_wall.view", "freedom_wall.create", "freedom_wall.approve",
    "announcements.view", "announcements.create", "announcements.update", "announcements.archive",
]

STAFF_PERMISSIONS = [
    "users.view", "users.update", "users.archive", "users.password_reset",
    "books.view", "books.create", "books.update", "books.archive",
    "copies.view", "copies.create", "copies.update",
    "loans.create", "loans.return",
    "requests.process", "requests.view",
    "categories.manage",
    "freedom_wall.view", "freedom_wall.approve",
    "announcements.view", "announcements.create", "announcements.update", "announcements.archive",
]

MEMBER_PERMISSIONS = [
    "books.view",
    "loans.view",
    "requests.view",
    "freedom_wall.view", "freedom_wall.create",
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

        from django.conf import settings
        if not User.objects.filter(lrn=settings.ADMIN_LRN).exists():
            admin = User(
                lrn=settings.ADMIN_LRN,
                first_name="System",
                last_name="Administrator",
                role=admin_role,
                must_change_password=True,
            )
            admin.set_password(settings.ADMIN_PASSWORD)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {settings.ADMIN_LRN}"))

        from core.models import AboutConfig
        config = AboutConfig.get_config()
        if not config.data.get("school_years"):
            config.data["school_years"] = [
                {
                    "school_year": "2020-2021",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Angelo B. Reyes",
                        "Bianca Marie S. dela Cruz",
                        "Carlo P. Mendoza",
                        "Dianne R. Villanueva",
                        "Efraim J. Santos",
                    ],
                },
                {
                    "school_year": "2021-2022",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Angelo B. Reyes",
                        "Bianca Marie S. dela Cruz",
                        "Francis L. Ocampo",
                        "Gabrielle T. Rivera",
                        "Hannah F. de Guzman",
                        "Jose Mari D. Aquino",
                    ],
                },
                {
                    "school_year": "2022-2023",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Francis L. Ocampo",
                        "Gabrielle T. Rivera",
                        "Kimberly Anne C. Tolentino",
                        "Luis Miguel S. Rosario",
                        "Maria Sofia V. Domingo",
                        "Nathan E. Salvador",
                        "Patricia Joy L. Angeles",
                    ],
                },
                {
                    "school_year": "2023-2024",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Kimberly Anne C. Tolentino",
                        "Luis Miguel S. Rosario",
                        "Nathan E. Salvador",
                        "Patricia Joy L. Angeles",
                        "Rafael T. Marquez",
                        "Samantha Claire B. Enriquez",
                        "Theodore A. Gonzales",
                        "Ysabelle Rae P. Fernandez",
                    ],
                },
                {
                    "school_year": "2024-2025",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Rafael T. Marquez",
                        "Samantha Claire B. Enriquez",
                        "Theodore A. Gonzales",
                        "Ysabelle Rae P. Fernandez",
                        "Andrea Nicole D. Villamor",
                        "Carlos Joaquin L. Torres",
                        "Danica Marie O. Salvador",
                        "Emmanuel G. Cabrera",
                    ],
                },
                {
                    "school_year": "2025-2026",
                    "is_current": True,
                    "teacher_librarians": [
                        {
                            "name": "Ma. Cristina S. Dela Rosa",
                            "bio": "Designated teacher librarian overseeing library operations, collection development, and student reading programs.",
                        }
                    ],
                    "volunteers": [
                        "Andrea Nicole D. Villamor",
                        "Carlos Joaquin L. Torres",
                        "Danica Marie O. Salvador",
                        "Emmanuel G. Cabrera",
                        "Francesca May V. Austria",
                        "Kristoffer James C. Manalo",
                        "Lorenz Andrei P. Bautista",
                        "Margaux Elise F. Dimaculangan",
                        "Paolo Victor R. Hernandez",
                    ],
                },
                {
                    "school_year": "2026-2027",
                    "teacher_librarians": [],
                    "volunteers": [
                        "Francesca May V. Austria",
                        "Kristoffer James C. Manalo",
                        "Lorenz Andrei P. Bautista",
                        "Margaux Elise F. Dimaculangan",
                        "Paolo Victor R. Hernandez",
                        "Regine Anne C. Velasco",
                        "Sean Marcus T. Aguilar",
                        "Trixia Joy P. Labrador",
                        "Vincent Rafael M. Bartolome",
                        "Zara Bianca Q. Mercado",
                    ],
                },
            ]
            config.save()
            self.stdout.write(self.style.SUCCESS("Seeded about page configuration."))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))