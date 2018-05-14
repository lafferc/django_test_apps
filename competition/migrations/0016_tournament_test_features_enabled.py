# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0015_auto_20180303_2126'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='test_features_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
