# Generated by Django 5.0.8 on 2024-10-01 18:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0007_test_gradedtest'),
    ]

    operations = [
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the material.', max_length=100)),
                ('description', models.TextField(blank=True, help_text='A description of the material.')),
                ('file', models.FileField(help_text='File containing the material.', upload_to='materials/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(help_text='The course the material is associated with.', on_delete=django.db.models.deletion.CASCADE, to='selfgrade.course')),
            ],
        ),
    ]