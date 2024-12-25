from rest_framework import serializers
from .models import Job
from .functions import generate_job_description

class JobSerializer(serializers.ModelSerializer):
    job_description = serializers.CharField(allow_blank=True, required=False)
    evaluation_criteria = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Job
        fields = ['company_name', 'role', 'skills', 'project_experience', 'other_details', 'job_description', 'evaluation_criteria']

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
            job_description, evaluation_criteria = generate_job_description(role, skills, project_experience, other_details)

        # Update the instance with the new data
        instance.role = role
        instance.skills = skills
        instance.project_experience = project_experience
        instance.other_details = other_details
        instance.job_description = job_description
        instance.evaluation_criteria = evaluation_criteria

        instance.save()
        return instance
