# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0003_auto_20141120_0131'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='count',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
