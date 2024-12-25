from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import JobSerializer
from .models import Job

class JobCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            return Response({
                "message": "Job created successfully",
                "job": JobSerializer(job).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobUpdateView(APIView):
    def put(self, request, pk, *args, **kwargs):
        try:
            # Get the Job instance by primary key (pk)
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"message": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use the JobSerializer to validate and update the job data
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            updated_job = serializer.save()
            return Response({
                "message": "Job updated successfully",
                "job": JobSerializer(updated_job).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
