from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ASSISTANT = 'ASSISTANT', 'Booth Assistant'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.OWNER)
    contact_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username