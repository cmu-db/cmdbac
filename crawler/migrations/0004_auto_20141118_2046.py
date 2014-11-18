# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0003_auto_20141118_1958'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='repository',
            name='repo_name',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='user_name',
        ),
    ]
