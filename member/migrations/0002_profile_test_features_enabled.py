# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='test_features_enabled',
            field=models.BooleanField(default=False, help_text=b'This user can use features that are under test'),
        ),
    ]
