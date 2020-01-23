# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0004_profile_cookie_consent'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='logo',
            field=models.ImageField(null=True, upload_to=b'images/', blank=True),
        ),
    ]
