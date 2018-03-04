# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import competition.models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0014_auto_20180302_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='postponed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='year',
            field=models.IntegerField(default=competition.models.current_year, choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019)]),
        ),
    ]
