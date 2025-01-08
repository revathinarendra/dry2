import uuid
from django.db import models



#Create your models here.

class Job(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    job_company_name = models.CharField(max_length=255,default="Glint AI")
    role = models.CharField(max_length=200)
    skills = models.TextField()
    project_experience = models.CharField(max_length=255)
    other_details = models.TextField()
    job_description = models.TextField(null=True, blank=True)
    evaluation_criteria = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, default="Default Location")
    job_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.pk} - {self.role} ({self.get_job_status_display()})"
  

    
class Profile(models.Model):
    resume_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15,null=True)
    email = models.EmailField(max_length=200,null=True)
    role = models.CharField(max_length=200,null=True)
    resume_text = models.TextField()

    def __str__(self):
        return str(self.pk)

class Recruitment(models.Model):
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='recruitments')
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recruitment_profiles')
    status = models.CharField(max_length=200)
    questions = models.TextField(null=True)
    transcript = models.TextField(null=True)
    interview_feedback = models.TextField(null=True)
    matching_percentage = models.CharField(max_length=5,null=True)

    def __str__(self):
        return self.pk

