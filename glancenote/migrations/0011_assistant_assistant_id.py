# Generated by Django 5.0 on 2023-12-17 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("glancenote", "0010_remove_assignmentcompletion_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistant",
            name="assistant_id",
            field=models.CharField(max_length=255, null=True),
        ),
    ]