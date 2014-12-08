# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0002_attempt_repo'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='base_dir',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attempt',
            name='setting_dir',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
    ]
