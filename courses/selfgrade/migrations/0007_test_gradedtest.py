# Generated by Django 5.0.8 on 2024-09-16 18:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0006_assignment_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the test.', max_length=100)),
                ('max_points', models.PositiveSmallIntegerField(help_text='The maximum points achievable on the test.')),
                ('weight', models.PositiveSmallIntegerField(help_text='The percentage of the total grade.')),
                ('course', models.ForeignKey(help_text='The course this test belongs to.', on_delete=django.db.models.deletion.CASCADE, to='selfgrade.course')),
            ],
        ),
        migrations.CreateModel(
            name='GradedTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.PositiveIntegerField(blank=True, help_text='The points the student received.', null=True)),
                ('registration', models.ForeignKey(help_text="The student's registration.", on_delete=django.db.models.deletion.CASCADE, to='selfgrade.registration')),
                ('test', models.ForeignKey(help_text='The test being graded.', on_delete=django.db.models.deletion.CASCADE, to='selfgrade.test')),
            ],
            options={
                'unique_together': {('registration', 'test')},
            },
        ),
    ]