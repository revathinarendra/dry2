
from django.urls import path
from .views import JobCreateView, JobDetailView, JobUpdateView, UploadResumeView

urlpatterns = [
    path('jobs/', JobCreateView.as_view(), name='job-create'),
    path('updatejobs/<int:pk>/', JobUpdateView.as_view(), name='job-update'), 
    path('jobs/<int:id>/', JobDetailView.as_view(), name='job-detail'),
    path('profile/register/', UploadResumeView.as_view(), name='upload-resume'),
    path('profile/details/<str:resume_id>/', UploadResumeView.as_view(), name='get_resume'),
]
