# Generated by Django 4.2.4 on 2025-01-06 06:58

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('recruit', '0004_alter_job_evaluation_criteria_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='resume_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
