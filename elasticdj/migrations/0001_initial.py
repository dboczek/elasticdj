# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-21 01:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(choices=[(b'rebuild', b'rebuild'), (b'update', b'update')], editable=False, max_length=7)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(editable=False, null=True)),
            ],
        ),
    ]
