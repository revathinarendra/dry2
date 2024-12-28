from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import JobSerializer, ProfileSerializer
from .models import Job,Profile
from rest_framework.generics import RetrieveAPIView
from .functions import  extract_text_from_docx, extract_text_from_pdf, find_matching_profiles, generate_uuid, save_metadata_to_json, upload_resume_to_cloud,fetch_resume_from_cloud 
from utils.encryption import encrypt_id,decrypt_id
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
import boto3
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView

# Define Pagination Class 
class JobPagination(PageNumberPagination):
    page_size = 20  # Number of records per page
    page_size_query_param = 'page_size'  # Allow clients to set the page size
    max_page_size = 100  # Maximum number of records per page

class JobCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            encrypted_id = encrypt_id(job.id)
            return Response({
                "message": "Job created successfully",
                "job": JobSerializer(job).data,
                "encrypted_id": encrypted_id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobUpdateView(APIView):
    def put(self, request, encrypted_id, *args, **kwargs):
        try:
            # Decrypt the ID
            job_id = decrypt_id(encrypted_id)
            # Get the Job instance by primary key (pk)
            job = Job.objects.get(id=job_id)
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

class JobDetailView(ListAPIView):
    serializer_class = JobSerializer
    pagination_class = JobPagination

    def get_queryset(self):
        return Job.objects.all().order_by('-id')  # Default ordering by ID descending

    def list(self, request, encrypted_id=None, *args, **kwargs):
        try:
            # Decrypt the ID if provided
            if encrypted_id:
                job_id = decrypt_id(encrypted_id)
                queryset = self.get_queryset().filter(id=job_id)
            else:
                queryset = self.get_queryset()

            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            # If no pagination is applied
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UploadResumeView(APIView):
    pagination_class = JobPagination 
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('resumes')  # Use getlist to handle multiple files
        if not files:
            return Response({"error": "No files uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        for file in files:
            try:
                # Generate a unique resume_id
                resume_id = generate_uuid()

                # Upload the file to S3 and get the stored file name
                stored_file_name = upload_resume_to_cloud(file, file.name, resume_id)

                # Determine file type and extract text
                if file.name.lower().endswith('.pdf'):
                    resume_text = extract_text_from_pdf(file)
                elif file.name.lower().endswith('.docx'):
                    resume_text = extract_text_from_docx(file)
                elif file.name.lower().endswith('.txt'):
                    resume_text = file.read().decode('utf-8')
                else:
                    return Response({"error": f"Unsupported file type for {file.name}"}, 
                                    status=status.HTTP_400_BAD_REQUEST)
                
                # Extract fields from the resume text (e.g., name, contact info, etc.)
                extracted_data = find_matching_profiles(resume_text)
                extracted_data['resume_id'] = resume_id
                extracted_data['resume_text'] = resume_text

                # Save to the database
                serializer = ProfileSerializer(data=extracted_data)
                if serializer.is_valid():
                    profile = serializer.save()  # Save the profile to the database

                    # Save metadata to a JSON file (optional)
                    save_metadata_to_json(extracted_data)

                    response_data.append({
                        "message": f"Resume {file.name} uploaded successfully",
                        "profile_data": serializer.data
                    })
                else:
                    response_data.append({
                        "error": f"Validation failed for {file.name}",
                        "details": serializer.errors
                    })
            except Exception as e:
                response_data.append({
                    "error": f"Error processing {file.name}: {str(e)}"
                })

        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)


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
            # Retrieve all profiles with pagination
            profiles = Profile.objects.all()
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(profiles, request)
            if page is not None:
                serializer = ProfileSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            # If no pagination is applied
            serializer = ProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class FetchResumeView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the resume_id from the query parameters
        resume_id = request.query_params.get('resume_id')

        if not resume_id:
            return Response({"error": "Resume ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the resume_id exists in the Profile model
        try:
            profile = Profile.objects.get(resume_id=resume_id)
        except Profile.DoesNotExist:
            return Response({"error": "Resume not found for the provided resume ID"}, 
                            status=status.HTTP_404_NOT_FOUND)

        
        # fetch resume from s3 bucket
        resume_content = fetch_resume_from_cloud(profile.resume_id)

        return Response({
            "resume_id": resume_id,
            "name": profile.name,
            "role": profile.role,
            "resume_text": resume_content  
        }, status=status.HTTP_200_OK)
