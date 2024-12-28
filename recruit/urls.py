
from django.urls import path
from .views import FetchResumeView, JobCreateView, JobDetailView, JobUpdateView, UploadResumeView, fetch_resume

urlpatterns = [
    path('jobs/', JobCreateView.as_view(), name='job-create'),
    path('updatejobs/<str:encrypted_id>/', JobUpdateView.as_view(), name='job-update'), 
    path('jobs/<str:encrypted_id>/', JobDetailView.as_view(), name='job-detail'),
    path('profile/register/', UploadResumeView.as_view(), name='upload-resume'),
    path('profile/details/<str:encrypted_resume_id>/', UploadResumeView.as_view(), name='get_resume'),
    path('fetch-resume/', FetchResumeView.as_view(), name='fetch_resume'),
]
