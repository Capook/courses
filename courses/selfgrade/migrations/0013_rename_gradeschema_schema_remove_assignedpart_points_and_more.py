# Generated by Django 5.0.8 on 2024-12-28 16:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0012_gradeschema_description_schemaitem_description'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GradeSchema',
            new_name='Schema',
        ),
        migrations.RemoveField(
            model_name='assignedpart',
            name='points',
        ),
        migrations.AddField(
            model_name='assignedpart',
            name='schema',
            field=models.ForeignKey(default=0, help_text='The grading scheme for this item.', on_delete=django.db.models.deletion.CASCADE, to='selfgrade.schema'),
            preserve_default=False,
        ),
    ]