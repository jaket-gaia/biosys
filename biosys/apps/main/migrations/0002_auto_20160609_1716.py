# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-09 09:16
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='data',
            new_name='attributes',
        ),
        migrations.RemoveField(
            model_name='project',
            name='dataset',
        ),
        migrations.AddField(
            model_name='project',
            name='attributes_descriptor',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]