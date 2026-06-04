from django.urls import path
from . import views

app_name = "loans"

urlpatterns = [
    path("", views.loan_list_view, name="loan_list"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("checkout/copy/", views.checkout_select_copy, name="checkout_select_copy"),
    path("checkout/confirm/", views.checkout_confirm, name="checkout_confirm"),
    path("return/", views.return_book_view, name="return_book"),
    path("return/<str:loan_id>/confirm/", views.return_confirm, name="return_confirm"),
    path("overdue/", views.overdue_list_view, name="overdue_list"),
    path("user/<str:lrn>/", views.user_loans_view, name="user_loans"),
]