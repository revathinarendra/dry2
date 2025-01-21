from rest_framework import serializers
from utils.encryption import encrypt_id
from .models import Job,Profile, Recruitment
import asyncio
from rest_framework import serializers
from .models import Job
from geminai import generate_interview_questions, generate_job_description, generate_evaluation_criteria

class JobSerializer(serializers.ModelSerializer):
    encrypted_id = serializers.SerializerMethodField()
    decrypted_id = serializers.IntegerField(source="id", read_only=True)
    job_description = serializers.CharField(allow_blank=True, required=False)
    evaluation_criteria = serializers.CharField(allow_blank=True, required=False)
    
    class Meta:
        model = Job
        fields = [
             'encrypted_id','decrypted_id','job_company_name','role', 'skills', 'project_experience',
            'other_details', 'job_description', 'evaluation_criteria', 'location','job_status','linkedin_response','created_at','updated_at'
        ]
    def get_encrypted_id(self, obj):
        # Generate the encrypted ID 
        return f"job-{obj.id:04d}"
    async def async_generate_details(self, job_company_name, role, skills, project_experience, other_details):
        try:
            # Generate job description using the helper function
            job_description = await generate_job_description({
                'role': role,
                'job_company_name': job_company_name,
                'skills': skills,
                'project_experience': project_experience,
                'other_details': other_details
            })

            # Generate evaluation criteria
            evaluation_criteria = await generate_evaluation_criteria(
                {'role': role, 'job_company_name': job_company_name, 'skills': skills},
                job_description
            )

            return job_description or "", evaluation_criteria or ""
        except Exception as e:
            # Log the error
            print(f"Error in async_generate_details: {e}")
            return "", ""

    def update(self, instance, validated_data):
        # Extract fields from validated data
        job_company_name = validated_data.get('job_company_name', instance.job_company_name)
        role = validated_data.get('role', instance.role)
        skills = validated_data.get('skills', instance.skills)
        project_experience = validated_data.get('project_experience', instance.project_experience)
        other_details = validated_data.get('other_details', instance.other_details)

        # Extract or generate job description and evaluation criteria
        job_description = validated_data.get('job_description', instance.job_description)
        evaluation_criteria = validated_data.get('evaluation_criteria', instance.evaluation_criteria)

        if not job_description or not evaluation_criteria:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            job_description, evaluation_criteria = loop.run_until_complete(
                self.async_generate_details(job_company_name, role, skills, project_experience, other_details)
            )
            loop.close()

        # Update instance fields
        instance.job_company_name = job_company_name
        instance.role = role
        instance.skills = skills
        instance.project_experience = project_experience
        instance.other_details = other_details
        instance.job_description = job_description
        instance.evaluation_criteria = evaluation_criteria

        instance.save()
        return instance

class RecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = [
            'id',
            'job_id',
            'profile_id',
            'status',
            'questions',
            'transcript',
            'interview_feedback',
            'matching_percentage',
            'interview_time',
            'interview_link',
        ]

    def create(self, validated_data):
        # Hardcode default values if they are not provided
        validated_data.setdefault('status', "In Progress")
        validated_data.setdefault('matching_percentage', "100%")
        validated_data.setdefault('interview_time', "not yet scheduled")

        # Save the instance with the modified data
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Check if the profile has been updated to generate new interview questions
        resume_text = validated_data.get('profile_id').resume_text if validated_data.get('profile_id') else instance.profile_id.resume_text
        job_description = instance.job_id.description
        evaluation_criteria = instance.job_id.evaluation_criteria

        # Generate interview questions based on job description, evaluation criteria, and resume text
        questions = generate_interview_questions(job_description, evaluation_criteria, resume_text)
        validated_data['questions'] = questions  # Set the generated questions in the validated data

        # Call the parent update method to update the instance
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Override to_representation to ensure the 'questions' field is replaced with
        a custom message if no questions are available.
        """
        data = super().to_representation(instance)

        # If questions field is empty or None, replace with the custom message
        if not data.get('questions'):
            data['questions'] = "No interview questions found for this recruitment."

        return data

class ProfileSerializer(serializers.ModelSerializer):
    encrypted_profile_id = serializers.IntegerField(source="id", read_only=True)
    recruitment_profiles = RecruitmentSerializer(many=True, read_only=True)  # Include recruitment details

    class Meta:
        model = Profile
        fields = [
            'id',
            'encrypted_profile_id',
            'resume_id',
            'name',
            'mobile',
            'email',
            'role',
            'resume_text',
            'recruitment_profiles',  
        ]
        read_only_fields = ['resume_id']
