# Generated by Django 5.0.8 on 2024-12-27 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selfgrade', '0009_alter_material_options_material_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignment',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='assignedpart',
            name='rubric',
            field=models.TextField(blank=True, help_text='A rubric for the grading of this part.'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='order'),
            preserve_default=False,
        ),
    ]
