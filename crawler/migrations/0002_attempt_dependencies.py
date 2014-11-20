# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='dependencies',
            field=models.ManyToManyField(to='crawler.Package', through='crawler.Dependency'),
            preserve_default=True,
        ),
    ]
