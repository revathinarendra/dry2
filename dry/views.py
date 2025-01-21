from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from linkedin import post_job_to_linkedin

def home(request):
    return HttpResponse("Welcome to the homepage!")

class PostJobToLinkedInView(APIView):
    def post(self, request):
        job_details = request.data
        result = post_job_to_linkedin(job_details)

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)
