# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import competition.models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0021_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='match_id',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='state',
            field=models.IntegerField(default=1, choices=[(0, b'Pending'), (1, b'Active'), (2, b'Finished'), (3, b'Archived')]),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(default=competition.models.current_year, choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021)]),
        ),
    ]
