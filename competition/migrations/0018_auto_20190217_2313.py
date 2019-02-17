# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import competition.models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0017_remove_tournament_display_margin_per_game'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(default=competition.models.current_year, choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020)]),
        ),
    ]
