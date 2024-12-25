
from django.urls import path
from .views import JobCreateView, JobUpdateView

urlpatterns = [
    path('jobs/', JobCreateView.as_view(), name='job-create'),
    path('jobs/<int:pk>/', JobUpdateView.as_view(), name='job-update'),  # PUT method for updating a job
]
