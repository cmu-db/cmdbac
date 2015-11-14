# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_auto_20150530_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='markup',
            field=models.CharField(max_length=25, choices=[('markdown', 'Markdown')]),
        ),
    ]
