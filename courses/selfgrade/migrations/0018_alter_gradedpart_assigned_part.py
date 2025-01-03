# Generated by Django 5.0.8 on 2024-12-30 20:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0017_gradedpart_part'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradedpart',
            name='assigned_part',
            field=models.ForeignKey(help_text='The specific part being graded.', null=True, on_delete=django.db.models.deletion.CASCADE, to='selfgrade.assignedpart'),
        ),
    ]
