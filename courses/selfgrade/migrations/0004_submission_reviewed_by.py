# Generated by Django 5.0.8 on 2024-08-12 17:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0003_alter_gradedpart_unique_together_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, help_text='The user who reviewed the submission.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]