# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-22 05:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_rename_title_comments_add_description_20170622_1103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='site',
            name='parent_site',
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(help_text='Enter a name for the project (required).', max_length=300, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='site',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
    ]