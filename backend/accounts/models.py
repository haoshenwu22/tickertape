from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model. Uses Django's built-in is_staff as the admin flag."""

    class Meta:
        ordering = ["-date_joined"]
