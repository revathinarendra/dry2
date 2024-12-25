from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from dry import settings  
from django.utils.text import slugify
import uuid


class MyAccountManager(BaseUserManager):
    def create_user(self, username, email, company_name,password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError("User must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            company_name=company_name,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,  email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superadmin', True)

        return self.create_user( email, username, password, **extra_fields)


class Account(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True,blank=True)
    email = models.EmailField(max_length=100, unique=True)
    company_name = models.CharField(max_length=255,null=True,blank=True)
    
    # required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = MyAccountManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email  # Set username to email if not provided
        super().save(*args, **kwargs)


    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True







