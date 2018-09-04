# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-28 07:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_auto_20180704_1808'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=main.models.get_dataset_media_path)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Dataset')),
            ],
            options={
                'verbose_name_plural': 'dataset_media',
            },
        ),
        migrations.CreateModel(
            name='ProjectMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=main.models.get_project_media_path)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Project')),
            ],
            options={
                'verbose_name_plural': 'project_media',
            },
        ),
    ]