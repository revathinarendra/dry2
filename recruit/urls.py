
from django.urls import path
from .views import FetchResumeView, InterviewCandidatesView, InterviewFeedbackView, InterviewQuestionView, InterviewQuestionsView, JobCreateView, JobDetailView, JobProfileDetailsView, JobUpdateView, ProfileDetailView, ProfileListView, UpdateInterviewTimeView, UploadResumeView

urlpatterns = [
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('jobs/update/<str:encrypted_id>/', JobUpdateView.as_view(), name='job-update'), 
    path('jobs/', JobDetailView.as_view(), name='job-list'),
    path('jobs/<str:encrypted_id>/', JobDetailView.as_view(), name='job-detail'),
    path('profile/create/<str:encrypted_id>/', UploadResumeView.as_view(), name='upload-resume'),
    path('profile/', UploadResumeView.as_view(), name='get_resume'),
    path('profile/resume/<str:encrypted_profile_id>/', FetchResumeView.as_view(), name='fetch_resume'),
    path('profile/<encrypted_profile_id>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('job/find_profile/', ProfileListView.as_view(), name='find_profile'),
    path('jobs/profiles/<int:job_id>/', JobProfileDetailsView.as_view(), name='job-profile-details'),
    path('interview_schedule/<int:id>/', UpdateInterviewTimeView.as_view(), name='update_interview_time'),
    path('interview_candidates/', InterviewCandidatesView.as_view(), name='interview_candidates'),
    path('interview_feedback/', InterviewFeedbackView.as_view(), name='interview_feedback'),
    path('interview_questions/', InterviewQuestionsView.as_view(), name='interview_questions'),
    path('generate_interview_questions/<int:id>/', InterviewQuestionView.as_view(), name='generate_interview_questions'),
    
]
