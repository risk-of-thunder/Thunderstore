# Generated by Django 3.1.4 on 2020-12-20 13:21

from django.db import migrations, models


def set_default(apps, schema_editor):
    PackageVersion = apps.get_model("repository", "PackageVersion")
    for package in PackageVersion.objects.all().iterator():
        package.display_name = package.name.replace("_", " ")
        package.save()


class Migration(migrations.Migration):

    dependencies = [
        ("repository", "0022_add_package_listing"),
    ]

    operations = [
        migrations.AddField(
            model_name="packageversion",
            name="display_name",
            field=models.CharField(null=True, max_length=128),
            preserve_default=False,
        ),
        migrations.RunPython(set_default, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="packageversion",
            name="display_name",
            field=models.CharField(max_length=128),
            preserve_default=False,
        ),
    ]