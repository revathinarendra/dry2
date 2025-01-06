import PyPDF2
import docx
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from geminai import  fetch_resume_from_cloud, generate_evaluation_criteria, generate_job_description, read_resume, read_resume_type, upload_resume_to_cloud
from .serializers import JobSerializer, ProfileSerializer
from .models import Job,Profile
from .functions import generate_uuid
from utils.encryption import encrypt_id,decrypt_id
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from io import BytesIO

class JobPagination(PageNumberPagination):
    page_size = 20  # Number of records per page
    page_size_query_param = 'page_size'  # Allow clients to set the page size
    max_page_size = 100  # Maximum number of records per page



class JobCreateView(APIView):
    def post(self, request, *args, **kwargs):
        # Create a JobSerializer instance with the incoming data
        serializer = JobSerializer(data=request.data)
        
        # Check if the serializer is valid
        if serializer.is_valid():
            try:
                # Use a transaction to ensure atomicity
                with transaction.atomic():
                    # Save the job synchronously
                    job = serializer.save()

                    # Encrypt the job ID synchronously
                    encrypted_id = encrypt_id(job.id)

                    # Generate job description and evaluation criteria
                    job_description = generate_job_description({
                        "role": job.role,
                        "company_name": job.company_name,
                        "skills": job.skills,
                        "project_experience": job.project_experience,
                        "other_details": job.other_details
                    })

                    evaluation_criteria = generate_evaluation_criteria({
                        "role": job.role,
                        "company_name": job.company_name,
                        "skills": job.skills,
                        "project_experience": job.project_experience,
                        "other_details": job.other_details
                    }, job_description)

                    # Save additional data to the job model or related tables
                    job.job_description = job_description
                    job.evaluation_criteria = evaluation_criteria
                    job.save()

                # Return a successful response
                return Response({
                    "message": "Job created successfully",
                    "job": JobSerializer(job).data,
                    "encrypted_id": encrypted_id,
                    "job_description": job_description,
                    "evaluation_criteria": evaluation_criteria
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                # Rollback the transaction and return an error response
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If the serializer is not valid, return error details
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
        files = request.FILES.getlist('resumes')
        if not files:
            return Response({"error": "No files uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        for file in files:
            try:
                # Read file content into memory
                file_content = file.read()
            
                # Wrap file content in BytesIO for safe handling
                temp_file = BytesIO(file_content)
                temp_file.name = file.name  # Preserve the original file name

                # Generate a unique resume_id
                resume_id = generate_uuid()

                # Extract text based on file type
                resume_text = None
                if temp_file.name.lower().endswith('.pdf') or temp_file.name.lower().endswith('.docx'):
                    resume_text = read_resume_type(temp_file)
                elif temp_file.name.lower().endswith('.txt'):
                    temp_file.seek(0)  # Reset the pointer before reading text
                    resume_text = temp_file.read().decode('utf-8')
                else:
                    response_data.append({"error": f"Unsupported file type for {temp_file.name}"})
                    continue

                # Extract fields from resume text
                extracted_data = read_resume(resume_text)
                extracted_data['resume_id'] = resume_id
                extracted_data['resume_text'] = resume_text

                # Save to the database
                serializer = ProfileSerializer(data=extracted_data)
                if serializer.is_valid():
                    serializer.save()
                    response_data.append({
                        "message": f"Resume {temp_file.name} uploaded successfully",
                        "profile_data": serializer.data
                    })
                else:
                    response_data.append({
                        "error": f"Validation failed for {temp_file.name}",
                        "details": serializer.errors
                    })

                # Upload file to cloud storage (S3)
                temp_file.seek(0)  # Ensure the file pointer is at the start before uploading
                upload_resume_to_cloud(temp_file, temp_file.name, resume_id, file.content_type)

            except Exception as e:
                response_data.append({
                    "error": f"Error processing {file.name}: {str(e)}"
                })

        return Response(response_data, status=status.HTTP_207_MULTI_STATUS)


    def get(self, request, *args, **kwargs):
        resume_id = kwargs.get('resume_id', None)
        if resume_id:
            try:
                profile = Profile.objects.get(resume_id=resume_id)
                serializer = ProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Profile.DoesNotExist:
                return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            profiles = Profile.objects.all()
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(profiles, request)
            if page is not None:
                serializer = ProfileSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)




# class FetchResumeView(APIView):
#     def get(self, request, encrypted_profile_id, *args, **kwargs):
#         try:
#             # Decrypt the profile ID
#             decrypted_profile_id = decrypt_id(encrypted_profile_id)
#             profile = Profile.objects.get(id=decrypted_profile_id)
#         except Exception as e:
#             return Response({"error": "Invalid or malformed profile ID"}, 
#                             status=status.HTTP_400_BAD_REQUEST)

#         # Fetch the profile using the decrypted profile ID
#         try:
#             profile = Profile.objects.get(id=decrypted_profile_id)
#         except Profile.DoesNotExist:
#             return Response({"error": "Profile not found"}, 
#                             status=status.HTTP_404_NOT_FOUND)

#         # Fetch the resume content from the cloud
#         resume_content = fetch_resume_from_cloud(profile.resume_id)

#         return Response({
#             "resume_id": profile.resume_id,
#             "name": profile.name,
#             "role": profile.role,
#             "resume_text": resume_content  
#         }, status=status.HTTP_200_OK)



class FetchResumeView(APIView):
    def get(self, request, encrypted_profile_id, *args, **kwargs):
        try:
            # Decrypt the profile ID
            decrypted_profile_id = decrypt_id(encrypted_profile_id)
        except Exception as e:
            return Response({"error": "Invalid or malformed profile ID"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Fetch the profile using the decrypted profile ID
        try:
            profile = Profile.objects.get(id=decrypted_profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Serialize the profile using ProfileSerializer
        serializer = ProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileDetailView(APIView):
    def get(self, request, profile_id, *args, **kwargs):
        try:
            # Decrypt the profile ID
            decrypted_profile_id = decrypt_id(profile_id)
        except Exception as e:
            return Response({"error": "Invalid or malformed profile ID"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Fetch the profile using the decrypted profile ID
        try:
            profile = Profile.objects.get(id=decrypted_profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Serialize the profile data
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)