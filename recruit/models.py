from django.db import models
from accounts.models import Account

# Create your models here.
class Job(models.Model):

    company_name = models.ForeignKey(
        Account,  max_length=255,
        on_delete=models.CASCADE,  
        related_name="jobs"  
    )
    role = models.CharField(max_length=200)
    skills = models.TextField()
    project_experience = models.CharField(max_length=255)
    other_details = models.TextField()
    job_description = models.TextField()
    evaluation_criteria = models.TextField()

    def __str__(self):
        return self.pk
    
class Profile(models.Model):
    resume_id = models.CharField(max_length=200)#UUID generated along with name
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15,null=True)
    email = models.EmailField(max_length=200,null=True)
    role = models.CharField(max_length=200,null=True)
    resume_text = models.TextField()

    def __str__(self):
        return self.pk

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

