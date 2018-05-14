# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0016_tournament_test_features_enabled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tournament',
            name='display_margin_per_game',
        ),
    ]
