from django.db import models
from accounts.models import User
from inventory.models import BookCopy


class Loan(models.Model):
    loan_id = models.CharField(max_length=200, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name="loans")
    checkout_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="processed_loans")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checkout_date"]

    def save(self, *args, **kwargs):
        if not self.loan_id:
            self.loan_id = f"{self.checkout_date:%Y%m%d}-{self.user.lrn}-{self.book_copy.copy_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.loan_id

    @property
    def is_overdue(self):
        if self.return_date:
            return False
        from django.utils import timezone
        return timezone.localdate() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        from django.utils import timezone
        return (timezone.localdate() - self.due_date).days

    @property
    def days_until_due(self):
        from django.utils import timezone
        if self.return_date:
            return 0
        return (self.due_date - timezone.localdate()).days