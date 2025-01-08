
from django.urls import path
from .views import FetchResumeView, JobCreateView, JobDetailView, JobUpdateView, ProfileDetailView, ProfileListView, UploadResumeView

urlpatterns = [
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('jobs/update/<str:encrypted_id>/', JobUpdateView.as_view(), name='job-update'), 
    path('jobs/', JobDetailView.as_view(), name='job-list'),
    path('jobs/<str:encrypted_id>/', JobDetailView.as_view(), name='job-detail'),
    path('profile/create/', UploadResumeView.as_view(), name='upload-resume'),
    path('profile/', UploadResumeView.as_view(), name='get_resume'),
    path('profile/resume/<str:encrypted_profile_id>/', FetchResumeView.as_view(), name='fetch_resume'),
    path('profile/<str:profile_id>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('job/find_profile/', ProfileListView.as_view(), name='find_profile'),
    
]
