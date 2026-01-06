from django.db import models

class ContactMessage(models.Model):
    puskesmas = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # New field for read/unread status


    def __str__(self):
        return f"{self.puskesmas} - {self.email}"
    