from rest_framework import serializers
from utils.encryption import encrypt_id
from .models import Job,Profile
import asyncio
from rest_framework import serializers
from .models import Job
from geminai import generate_job_description, generate_evaluation_criteria



class JobSerializer(serializers.ModelSerializer):
    job_description = serializers.CharField(allow_blank=True, required=False)
    evaluation_criteria = serializers.CharField(allow_blank=True, required=False)
    
    class Meta:
        model = Job
        fields = [
             'id','job_company_name','role', 'skills', 'project_experience',
            'other_details', 'job_description', 'evaluation_criteria', 'location','job_status','created_at','updated_at'
        ]
    
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

class ProfileSerializer(serializers.ModelSerializer):
    encrypted_profile_id = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['encrypted_profile_id','resume_id', 'name', 'mobile', 'email', 'role', 'resume_text',]
        read_only_fields = ['resume_id']  # UUID is generated automatically
    def get_encrypted_profile_id(self, obj):
        """
        Return the encrypted profile ID.
        """
        return encrypt_id(obj.id)