# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0002_attempt_dependencies'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='local_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='attempt',
            unique_together=set([('repo', 'local_id')]),
        ),
    ]
