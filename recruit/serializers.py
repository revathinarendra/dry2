from rest_framework import serializers
from .models import Job,Profile
from .functions import generate_job_description
import asyncio

class JobSerializer(serializers.ModelSerializer):
    job_description = serializers.CharField(allow_blank=True, required=False)
    evaluation_criteria = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Job
        fields = ['company_name', 'role', 'skills', 'project_experience', 'other_details', 'job_description', 'evaluation_criteria']

    async def async_generate_details(self, role, skills, project_experience, other_details):
        # Simulate an async job description generation
        await asyncio.sleep(10)  
        return "Generated Job Description", "Generated Evaluation Criteria"

    def update(self, instance, validated_data):
        # Extract the fields from validated data
        role = validated_data.get('role', instance.role)
        skills = validated_data.get('skills', instance.skills)
        project_experience = validated_data.get('project_experience', instance.project_experience)
        other_details = validated_data.get('other_details', instance.other_details)

        # If job_description and evaluation_criteria are not provided, generate them
        job_description = validated_data.get('job_description', instance.job_description)
        evaluation_criteria = validated_data.get('evaluation_criteria', instance.evaluation_criteria)

        if not job_description or not evaluation_criteria:
            loop = asyncio.get_event_loop()
            job_description, evaluation_criteria = loop.run_until_complete(
                self.async_generate_details(role, skills, project_experience, other_details)
            )
            # job_description, evaluation_criteria = generate_job_description(role, skills, project_experience, other_details)

        # Update the instance with the new data
        instance.role = role
        instance.skills = skills
        instance.project_experience = project_experience
        instance.other_details = other_details
        instance.job_description = job_description
        instance.evaluation_criteria = evaluation_criteria

        instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['resume_id', 'name', 'mobile', 'email', 'role', 'resume_text']
        read_only_fields = ['resume_id']  # UUID is generated automatically
