# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0004_package_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='count',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
