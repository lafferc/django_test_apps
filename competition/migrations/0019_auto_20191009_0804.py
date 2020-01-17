# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0018_auto_20190217_2313'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='match',
            options={'verbose_name_plural': 'matches'},
        ),
    ]
