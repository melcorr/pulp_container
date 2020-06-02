# Generated by Django 2.2.12 on 2020-05-19 20:57

from django.db import migrations, models
import django.db.models.deletion
import pulp_container.app.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_import_export_validate_params'),
        ('container', '0003_oci_mediatype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('pulp_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pulp_created', models.DateTimeField(auto_now_add=True)),
                ('pulp_last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('offset', models.BigIntegerField(default=0)),
                ('file', models.FileField(max_length=255, null=True, upload_to=pulp_container.app.models.generate_filename)),
                ('size', models.IntegerField(null=True)),
                ('md5', models.CharField(max_length=32, null=True)),
                ('sha1', models.CharField(max_length=40, null=True)),
                ('sha224', models.CharField(max_length=56, null=True)),
                ('sha256', models.CharField(max_length=64, null=True)),
                ('sha384', models.CharField(max_length=96, null=True)),
                ('sha512', models.CharField(max_length=128, null=True)),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to='core.Repository')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]