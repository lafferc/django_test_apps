# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0003_auto_20180530_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='cookie_consent',
            field=models.PositiveIntegerField(default=0, help_text=b'The user consents to the following level of cookies', choices=[(0, b'accept all cookies'), (1, b'no advertising cookies'), (2, b'functional cookies only')]),
        ),
    ]
