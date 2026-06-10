from django.conf import settings


def create_demo_users():
    from accounts.models import User, Role
    from demo.models import DemoProfile

    admin_role = Role.objects.get(name="Administrator")
    staff_role = Role.objects.get(name="Staff")
    member_role = Role.objects.get(name="Member")

    demo_accounts = [
        {"lrn": "admin", "password": "admin", "first_name": "Demo", "last_name": "Administrator", "role": admin_role},
        {"lrn": "staff", "password": "staff", "first_name": "Demo", "last_name": "Staff", "role": staff_role},
        {"lrn": "student", "password": "student", "first_name": "Demo", "last_name": "Student", "role": member_role},
    ]

    for acct in demo_accounts:
        user, _ = User.objects.update_or_create(
            lrn=acct["lrn"],
            defaults={
                "first_name": acct["first_name"],
                "last_name": acct["last_name"],
                "role": acct["role"],
                "status": User.Status.ACTIVE,
                "must_change_password": False,
                "failed_login_attempts": 0,
                "locked_until": None,
            },
        )
        user.set_password(acct["password"])
        user.save(update_fields=["password"])
        DemoProfile.objects.get_or_create(user=user)
