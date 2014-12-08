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
            name='repo',
            field=models.ForeignKey(to='crawler.Repository', null=True),
            preserve_default=True,
        ),
    ]
