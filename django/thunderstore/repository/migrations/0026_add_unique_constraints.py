# Generated by Django 3.1.6 on 2021-03-07 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repository", "0025_alter_name_validator"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="discorduserbotpermission",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="package",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="packagerating",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="packageversion",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="packageversiondownloadevent",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="uploaderidentitymember",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="discorduserbotpermission",
            constraint=models.UniqueConstraint(
                fields=("thunderstore_user", "discord_user_id"),
                name="one_permission_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="package",
            constraint=models.UniqueConstraint(
                fields=("owner", "name"), name="unique_name_per_namespace"
            ),
        ),
        migrations.AddConstraint(
            model_name="packagerating",
            constraint=models.UniqueConstraint(
                fields=("rater", "package"), name="one_rating_per_rater"
            ),
        ),
        migrations.AddConstraint(
            model_name="packageversion",
            constraint=models.UniqueConstraint(
                fields=("package", "version_number"), name="unique_version_per_package"
            ),
        ),
        migrations.AddConstraint(
            model_name="packageversiondownloadevent",
            constraint=models.UniqueConstraint(
                fields=("version", "source_ip"), name="unique_counter_per_ip"
            ),
        ),
        migrations.AddConstraint(
            model_name="uploaderidentitymember",
            constraint=models.UniqueConstraint(
                fields=("user", "identity"), name="one_membership_per_user"
            ),
        ),
    ]
