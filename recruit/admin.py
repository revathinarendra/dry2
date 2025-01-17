from django.contrib import admin
from .models import Job, Profile, Recruitment

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_company_name', 'role', 'skills', 'project_experience','location','job_status','created_at','updated_at')
    search_fields = ('job_company_name__job_company_name', 'role') 
    list_filter = ('job_company_name',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'mobile', 'role', 'resume_id')
    search_fields = ('name', 'email', 'mobile', 'role')
    list_filter = ('role',)

@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_id', 'profile_id', 'status', 'matching_percentage','interview_time','interview_link')
    search_fields = ('status', 'job_id__company_name', 'profile_id__name')
    list_filter = ('status', 'job_id', 'profile_id')
    raw_id_fields = ('job_id', 'profile_id')
