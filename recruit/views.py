from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from geminai import generate_evaluation_criteria, generate_interview_questions, generate_job_description, read_resume, read_resume_type, read_transcription, upload_resume_to_cloud
from .serializers import JobSerializer, ProfileSerializer, RecruitmentSerializer
from .models import Job,Profile, Recruitment
from .functions import generate_uuid
from utils.encryption import encrypt_id,decrypt_id
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from io import BytesIO
from django.utils.timezone import now
from rest_framework.parsers import MultiPartParser, FormParser
import google.generativeai as genai
gemini_llm = genai.GenerativeModel("gemini-1.5-flash")
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
                    # encrypted_id = encrypt_id(job.id)

                    # Generate job description and evaluation criteria
                    job_description = generate_job_description({
                        "role": job.role,
                        "job_company_name": job.job_company_name,
                        "skills": job.skills,
                        "project_experience": job.project_experience,
                        "other_details": job.other_details
                    })

                    evaluation_criteria = generate_evaluation_criteria({
                        "role": job.role,
                        "job_company_name": job.job_company_name,
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
                    # "encrypted_id": encrypted_id,
                    "job_description": job_description,
                    "evaluation_criteria": evaluation_criteria
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                # Rollback the transaction and return an error response
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If the serializer is not valid, return error details
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class JobUpdateView(APIView):
    def put(self, request, *args, **kwargs):
        try:
            # Extract the decrypted_id from the request data
            decrypted_id = request.data.get('decrypted_id')
            if not decrypted_id:
                return Response({"message": "decrypted_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get the Job instance by the decrypted ID
            job = Job.objects.get(id=decrypted_id)
        except Job.DoesNotExist:
            return Response({"message": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Use the JobSerializer to validate and update the job data
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            updated_job = serializer.save()

            # Check if 'linkedin_saved' is in the request data
            linkedin_saved = request.data.get('linkedin_saved')
            if linkedin_saved is not None:
                # Perform any additional logic if needed
                pass

            return Response({
                "message": "Job updated successfully",
                "linkedin_saved": linkedin_saved,
                "job": JobSerializer(updated_job).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class JobListView(APIView):
    serializer_class = JobSerializer

    def get(self, request, *args, **kwargs):
        try:
            # Fetch all job records
            jobs = Job.objects.all()
            print(f"Number of jobs found: {jobs.count()}")

            # Serialize the job data
            serializer = self.serializer_class(jobs, many=True)
            print(f"Serialized data: {serializer.data}")

            # Return the serialized job data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class JobDetailView(APIView):
    serializer_class = JobSerializer

    def get(self, request, decrypted_id, *args, **kwargs):
        try:
            # Ensure decrypted_id is an integer
            if not isinstance(decrypted_id, int):
                raise ValueError("Invalid ID format")

            print(f"Fetching Job with ID: {decrypted_id}")
        
            # Fetch the specific job by ID
            job = Job.objects.get(id=decrypted_id)
            print(f"Job found: {job}")
        
            # Serialize the job data using the JobSerializer
            serializer = self.serializer_class(job)
            print(f"Serialized data: {serializer.data}")
        
            # Return the serialized job data
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"error": "Invalid ID format"}, status=status.HTTP_400_BAD_REQUEST)
        except Job.DoesNotExist:
            print("Job not found")
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UploadResumeView(APIView):
    pagination_class = JobPagination
    def decrypt_job_id(self,encrypted_id):
        # Check if encrypted_id is not None and starts with 'job-'
        print(f"Received encrypted_id: {encrypted_id}") 
        if encrypted_id and encrypted_id.startswith('job-'):
            try:
                # Extract the numeric part and convert it to an integer
                job_id = int(encrypted_id[4:])  # Skip 'job-' prefix and convert the rest to integer
                return job_id
            except ValueError:
                # If the conversion fails, return None or raise an error
                return None
        return None



    def post(self, request, encrypted_id, *args, **kwargs):
        print(f"URL matched, encrypted_id: {encrypted_id}")
        # Retrieve the encrypted job ID from the URL
        #encrypted_id = kwargs.get('encrypted_id')
        
        # Decrypt the encrypted job ID to get the actual job ID
        job_id = self.decrypt_job_id(encrypted_id)
        print(f"job id,decrypted:{job_id}")
        if not job_id:
            return Response({"error": "Invalid encrypted job ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the job object using the decrypted job ID
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist('resumes')
        if not files:
            return Response({"error": "No files uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        for file in files:
            try:
                # Read file content into memory
                file_content = file.read()
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
                extracted_data['profile_id'] = job.id  # Associate with the job using the job_id

                # Save to the database
                serializer = ProfileSerializer(data=extracted_data)
                if serializer.is_valid():
                    profile = serializer.save()
                    response_data.append({
                        "message": f"Resume {temp_file.name} uploaded successfully",
                        "profile_data": serializer.data
                    })

                    
                    recruitment_data = {
                        'job_id': job.id,  
                        'profile_id': profile.id,
                    }
                    recruitment_serializer = RecruitmentSerializer(data=recruitment_data)
                    if recruitment_serializer.is_valid():
                        print("Recruitment serializer is valid")
                        recruitment_serializer.save()
                        response_data.append({
                        "message": f"Recruitment entry created for {temp_file.name}",
                        "recruitserializer": recruitment_serializer.data
                    })
                    else:
                        response_data.append({
                            "error": f"Failed to create recruitment entry for {temp_file.name}",
                            "details": recruitment_serializer.errors
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
            # paginator = self.pagination_class()
            # page = paginator.paginate_queryset(profiles, request)
            # if page is not None:
            #     serializer = ProfileSerializer(page, many=True)
            #     return paginator.get_paginated_response(serializer.data)

            serializer = ProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateInterviewTimeView(APIView):
    def put(self, request, id, *args, **kwargs):
        print(f"Received recruitment_id: {id}") 
        try:
            # Retrieve the recruitment instance
            recruitment = Recruitment.objects.get(id=id)
        except Recruitment.DoesNotExist:
            return Response({"error": "Recruitment entry not found"}, status=status.HTTP_404_NOT_FOUND)

        # Extract the new interview time from the request data
        interview_time = request.data.get("interview_time")
        if not interview_time:
            return Response({"error": "No interview time provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update the interview_time field
            recruitment.interview_time = interview_time
            recruitment.save()
            return Response({
                "message": "Interview time updated successfully",
                "recruitment_data": RecruitmentSerializer(recruitment).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to update interview time: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchResumeView(APIView):
    def get(self, request, encrypted_profile_id, *args, **kwargs):
        # Use the encrypted_profile_id directly to fetch the profile
        try:
            profile = Profile.objects.get(id=encrypted_profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Serialize the profile using ProfileSerializer
        serializer = ProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)





class ProfileDetailView(APIView):
    def get(self, request, encrypted_profile_id, *args, **kwargs):
        #try:
            # Decrypt the profile ID
            #decrypted_profile_id = decrypt_id(profile_id)
        #except Exception as e:
            #return Response({"error": "Invalid or malformed profile ID"}, 
                            #status=status.HTTP_400_BAD_REQUEST)

        # Fetch the profile using the decrypted profile ID
        try:
            profile = Profile.objects.get(id=encrypted_profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Serialize the profile data
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileListView(APIView):
    """
    View to list all profiles or retrieve a specific profile by resume_id.
    """

    def get(self, request, *args, **kwargs):
        resume_id = request.query_params.get('resume_id', None)  # Get resume_id from query params
        if resume_id:
            try:
                profile = Profile.objects.get(resume_id=resume_id)
                serializer = ProfileSerializer(profile)
                data = serializer.data
                # Add default values
                data['status'] = "active"
                data['percentage_matching'] = "50%"
                return Response(data, status=status.HTTP_200_OK)
            except Profile.DoesNotExist:
                return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            profiles = Profile.objects.all()
            serializer = ProfileSerializer(profiles, many=True)
            data = serializer.data
            # Add default values to each profile in the list
            for profile_data in data:
                profile_data['status'] = "active"
                profile_data['percentage_matching'] = "50%"
            return Response(data, status=status.HTTP_200_OK)



class JobProfileDetailsView(APIView):
    def get(self, request, job_id):
        try:
            # Fetch recruitment records for the given job_id
            recruitment_records = Recruitment.objects.filter(job_id=job_id)

            if not recruitment_records.exists():
                return Response({"detail": "No records found for the given job ID."}, status=status.HTTP_404_NOT_FOUND)

            # Fetch the job details
            job = Job.objects.filter(id=job_id).first()
            if not job:
                return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

            # Serialize job details
            job_data = JobSerializer(job).data

            # Fetch profiles related to recruitment records and include recruitment details
            profiles = Profile.objects.filter(id__in=recruitment_records.values_list('profile_id', flat=True))
            profiles_data = ProfileSerializer(profiles, many=True).data

            # Prepare the response data
            response_data = {
                "job_details": job_data,
                "profiles": profiles_data,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Interview schedule details

class InterviewCandidatesView(APIView):
    def get(self, request):
        # Filter Recruitment records with present or future interview_time and exclude invalid cases
        recruitments = Recruitment.objects.filter(
            interview_time__gte=now()
        ).exclude(interview_time__isnull=True).exclude(interview_time="not yet scheduled")

        data = []
        for recruitment in recruitments:
            try:
                # Access the profile_id explicitly
                profile_id = recruitment.profile_id_id  # Use `_id` to get the integer ID
                profile = Profile.objects.get(id=profile_id)

                # Serialize both Profile and Recruitment data
                profile_data = ProfileSerializer(profile).data
                recruitment_data = RecruitmentSerializer(recruitment).data

                # Combine data into a single response object
                data.append({
                    "profile": profile_data,
                    "recruitment": recruitment_data,
                    "job_id": recruitment.job_id.id,  # Access job_id explicitly as an ID
                })
            except Profile.DoesNotExist:
                return Response(
                    {"error": f"Profile with ID {profile_id} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Check if data is empty
        if not data:
            return Response({"message": "No candidates available for interviews."}, status=status.HTTP_200_OK)

        return Response(data, status=status.HTTP_200_OK)

# interview feedback view for get request

class InterviewFeedbackView(APIView):
    def get(self, request):
        # Fetch Recruitment records where interview_feedback is present
        recruitments_with_feedback = Recruitment.objects.exclude(interview_feedback__isnull=True).exclude(interview_feedback__exact='')

        if recruitments_with_feedback.exists():
            data = []
            for recruitment in recruitments_with_feedback:
                try:
                    # Fetch the related Profile using profile_id
                    profile = recruitment.profile_id
                    profile_data = ProfileSerializer(profile).data

                    # Add job_id and recruitment data
                    data.append({
                        "profile": profile_data,
                        "job_id": recruitment.job_id.id,  # Include job ID
                        "recruitment": RecruitmentSerializer(recruitment).data,
                    })
                except Profile.DoesNotExist:
                    return Response(
                        {"error": f"Profile with ID {recruitment.profile_id_id} does not exist."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            return Response(data, status=status.HTTP_200_OK)
        else:
            # If no feedback is found, return 201 with a message
            return Response({"message": "No interview feedback found."}, status=status.HTTP_201_CREATED)
# interview questions get


class InterviewQuestionsView(APIView):
    def get(self, request, id):
        try:
            # Fetch the specific Recruitment record by ID
            recruitment = Recruitment.objects.get(id=id)

            # Fetch the related Profile using profile_id
            profile = recruitment.profile_id
            profile_data = ProfileSerializer(profile).data

            # Serialize the recruitment object
            recruitment_data = RecruitmentSerializer(recruitment).data

            # Prepare the final response data
            data = {
                "profile": profile_data,
                "job_id": recruitment.job_id.id,  # Include job ID
                "recruitment": recruitment_data,
            }
            return Response(data, status=status.HTTP_200_OK)

        except Recruitment.DoesNotExist:
            # If the recruitment record is not found
            return Response(
                {"error": f"Recruitment with ID {id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

class InterviewQuestionView(APIView):
    def put(self, request, id):
        try:
            # Fetch the Recruitment instance using the provided ID
            recruitment = Recruitment.objects.get(id=id)

            # Fetch the associated job and profile details
            job = recruitment.job_id
            profile = recruitment.profile_id

            # Validate that the required fields are present
            if not job or not profile:
                return Response(
                    {"error": "Recruitment must have a valid job and profile associated."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate interview questions using job description, evaluation criteria, and resume text
            job_description = job.job_description
            evaluation_criteria = job.evaluation_criteria
            resume_text = profile.resume_text
            interview_questions = generate_interview_questions(job_description, evaluation_criteria, resume_text)

            # Update the recruitment instance with the generated questions
            recruitment.questions = interview_questions
            recruitment.save()

            # Serialize and return the updated recruitment instance
            serializer = RecruitmentSerializer(recruitment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Recruitment.DoesNotExist:
            return Response({"error": "Recruitment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# generated transcript and feedback with file
class GenerateTranscriptView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, id, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and extract text from the file
        transcript_text = read_transcription(file)
        if not transcript_text:
            return Response({"error": "Invalid file type or unable to extract text."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the recruitment object using the id from the URL
            recruitment = Recruitment.objects.get(id=id)

            # Get candidate name and company from related models
            candidate_name = recruitment.profile_id.name
            company_name = recruitment.job_id.job_company_name

            # Save transcript to the model
            recruitment.transcript = transcript_text

            # Generate LLM evaluation
            prompt = f"""
            Evaluate the candidate {candidate_name}'s performance in the interview based on the following transcription.
            Assess the candidate on areas such as communication, technical skills, problem-solving, and role-specific knowledge.
            Provide a profile summary and determine if the candidate is suitable for the role or not.

            Transcription:
            {transcript_text}
            """
            evaluation = gemini_llm.generate_content(prompt).text

            # Save feedback to the model
            recruitment.interview_feedback = evaluation
            recruitment.save()

            # Serialize and return the updated object
            serializer = RecruitmentSerializer(recruitment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Recruitment.DoesNotExist:
            return Response({"error": "Recruitment object not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
