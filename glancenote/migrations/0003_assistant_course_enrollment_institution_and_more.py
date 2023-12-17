# Generated by Django 5.0 on 2023-12-15 03:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("glancenote", "0002_alter_class_options_alter_studentclass_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Assistant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("files", models.JSONField(default=list)),
            ],
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name_plural": "Courses",
            },
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="glancenote.course",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "StudentClasses",
            },
        ),
        migrations.CreateModel(
            name="Institution",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("address", models.TextField()),
                ("website", models.CharField(max_length=200)),
                ("domains", models.JSONField(default=list)),
            ],
        ),
        migrations.CreateModel(
            name="ParentProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("gender", models.CharField(blank=True, max_length=10)),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("birthday", models.DateField(blank=True, null=True)),
                (
                    "photo",
                    models.ImageField(
                        blank=True, null=True, upload_to="profile_photos/"
                    ),
                ),
                ("registration_tokens", models.JSONField(default=list)),
                ("subscription", models.CharField(blank=True, max_length=100)),
                ("phone_verified", models.BooleanField(default=False)),
                ("email_verified", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="TeacherProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "photo",
                    models.ImageField(
                        blank=True, null=True, upload_to="teacher_photos/"
                    ),
                ),
                ("courses_taught", models.JSONField(default=list)),
                ("phone_verified", models.BooleanField(default=False)),
                ("email_verified", models.BooleanField(default=False)),
                ("registration_tokens", models.JSONField(default=list)),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("birthday", models.DateField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, max_length=10)),
                (
                    "courses",
                    models.ManyToManyField(
                        blank=True, related_name="teachers", to="glancenote.course"
                    ),
                ),
                (
                    "institution",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teachers",
                        to="glancenote.institution",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="Class",
        ),
        migrations.DeleteModel(
            name="StudentClass",
        ),
        migrations.RemoveField(
            model_name="assignment",
            name="assignment_id",
        ),
        migrations.RemoveField(
            model_name="assignment",
            name="class_id",
        ),
        migrations.RemoveField(
            model_name="assignmentcompletion",
            name="assignment_id",
        ),
        migrations.RemoveField(
            model_name="assignmentcompletion",
            name="class_id",
        ),
        migrations.RemoveField(
            model_name="assignmentcompletion",
            name="student_id",
        ),
        migrations.RemoveField(
            model_name="log",
            name="class_id",
        ),
        migrations.RemoveField(
            model_name="log",
            name="student_id",
        ),
        migrations.RemoveField(
            model_name="student",
            name="student_id",
        ),
        migrations.AddField(
            model_name="assignmentcompletion",
            name="student",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.student",
            ),
        ),
        migrations.AddField(
            model_name="log",
            name="student",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.student",
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.course",
            ),
        ),
        migrations.AddField(
            model_name="assignmentcompletion",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.course",
            ),
        ),
        migrations.AddField(
            model_name="log",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.course",
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="student",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.student",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="institution",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="students",
                to="glancenote.institution",
            ),
        ),
        migrations.AddField(
            model_name="parentprofile",
            name="student",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="glancenote.student",
            ),
        ),
        migrations.AddField(
            model_name="parentprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="assistant",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="glancenote.parentprofile",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="teacher",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="taught_courses",
                to="glancenote.teacherprofile",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="mentors",
            field=models.ManyToManyField(
                blank=True,
                related_name="mentored_students",
                to="glancenote.teacherprofile",
            ),
        ),
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]