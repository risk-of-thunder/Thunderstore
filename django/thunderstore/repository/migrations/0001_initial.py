# Generated by Django 2.1.2 on 2019-04-04 20:11

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import thunderstore.repository.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Package",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("is_active", models.BooleanField(default=True)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "uuid4",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "maintainers",
                    models.ManyToManyField(
                        blank=True,
                        related_name="maintaned_packages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="owned_packages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PackageVersion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                ("downloads", models.PositiveIntegerField(default=0)),
                ("name", models.CharField(max_length=128)),
                ("version_number", models.CharField(max_length=16)),
                ("website_url", models.CharField(max_length=1024)),
                ("description", models.CharField(max_length=256)),
                ("readme", models.TextField()),
                (
                    "file",
                    models.FileField(
                        upload_to=thunderstore.repository.models.get_version_zip_filepath
                    ),
                ),
                (
                    "icon",
                    models.ImageField(
                        upload_to=thunderstore.repository.models.get_version_png_filepath
                    ),
                ),
                ("uuid4", models.UUIDField(default=uuid.uuid4, editable=False)),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="repository.Package",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="packageversion",
            unique_together={("package", "version_number")},
        ),
        migrations.AlterUniqueTogether(
            name="package",
            unique_together={("owner", "name")},
        ),
    ]
