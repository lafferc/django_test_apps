# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-02-16 00:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0023_auto_20210131_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='draw_definition',
            field=models.CharField(blank=True, choices=[(b'normal_time', b'normal_time'), (b'extra_time', b'extra_time')], default=b'extra_time', max_length=20, null=True),
        ),
    ]