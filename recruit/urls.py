
from django.urls import path
from .views import FetchResumeView, GenerateTranscriptView, InterviewCandidatesView, InterviewFeedbackView, InterviewQuestionView, InterviewQuestionsView, JobCreateView, JobDetailView, JobListView, JobProfileDetailsView, JobUpdateView,  ProfileDetailView, ProfileListView, UpdateInterviewTimeView, UploadResumeView, linkedin_auth, linkedin_callback

urlpatterns = [
    path('linkedin/auth', linkedin_auth, name='linkedin_auth'),
    path('linkedin/callback', linkedin_callback, name='linkedin_callback'),
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('jobs/update/<str:encrypted_id>/', JobUpdateView.as_view(), name='job-update'), 
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('jobs/<int:decrypted_id>/', JobDetailView.as_view(), name='job-detail'),
    path('profile/create/<str:encrypted_id>/', UploadResumeView.as_view(), name='upload-resume'),
    path('profile/', UploadResumeView.as_view(), name='get_resume'),
    path('profile/resume/<str:encrypted_profile_id>/', FetchResumeView.as_view(), name='fetch_resume'),
    path('profile/<encrypted_profile_id>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('job/find_profile/', ProfileListView.as_view(), name='find_profile'),
    path('jobs/profiles/<int:job_id>/', JobProfileDetailsView.as_view(), name='job-profile-details'),
    path('interview_schedule/<int:id>/', UpdateInterviewTimeView.as_view(), name='update_interview_time'),
    path('interview_candidates/', InterviewCandidatesView.as_view(), name='interview_candidates'),
    path('interview_feedback/', InterviewFeedbackView.as_view(), name='interview_feedback'),
    path('interview_questions/<int:id>/', InterviewQuestionsView.as_view(), name='interview_questions'),
    path('generate_interview_questions/<int:id>/', InterviewQuestionView.as_view(), name='generate_interview_questions'),
    path('generate_transcript/<int:id>/', GenerateTranscriptView.as_view(), name='generate_transcript'),

]
