from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import JobSerializer, ProfileSerializer
from .models import Job,Profile
from rest_framework.generics import RetrieveAPIView
from .functions import  extract_text_from_docx, extract_text_from_pdf, find_matching_profiles, generate_uuid, save_metadata_to_json


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

class JobDetailView(RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def get(self, request, *args, **kwargs):
        try:
            job_id = kwargs.get('id')  # Extract the ID from the URL
            job = self.get_queryset().get(id=job_id)  # Retrieve the Job object
            serializer = self.get_serializer(job)  # Serialize the object
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        


class UploadResumeView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('resume')  # Get the uploaded file from frontend
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine file type and extract text
        try:
            if file.name.lower().endswith('.pdf'):
                resume_text = extract_text_from_pdf(file)
            elif file.name.lower().endswith('.docx'):
                resume_text = extract_text_from_docx(file)
            elif file.name.lower().endswith('.txt'):
                resume_text = file.read().decode('utf-8')
            else:
                return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error processing file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate UUID for the resume
        resume_id = generate_uuid()

        # Extract fields from the resume text
        extracted_data = find_matching_profiles(resume_text)
        extracted_data['resume_id'] = resume_id
        extracted_data['resume_text'] = resume_text

        # Save to the database
        serializer = ProfileSerializer(data=extracted_data)
        if serializer.is_valid():
            serializer.save()

            # Save metadata to a JSON file
            save_metadata_to_json(extracted_data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        resume_id = kwargs.get('resume_id', None)

        if resume_id:
            # Retrieve a specific profile by resume_id
            try:
                profile = Profile.objects.get(resume_id=resume_id)
                serializer = ProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Profile.DoesNotExist:
                return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Retrieve all profiles if no resume_id is provided
            profiles = Profile.objects.all()
            serializer = ProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
