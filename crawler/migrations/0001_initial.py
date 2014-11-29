# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField()),
                ('duration', models.FloatField(null=True)),
                ('log', models.TextField(default=b'')),
                ('hostname', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sha', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Dependency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attempt', models.ForeignKey(to='crawler.Attempt')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('version', models.CharField(max_length=200)),
                ('count', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('full_name', models.CharField(max_length=200, serialize=False, primary_key=True)),
                ('private', models.BooleanField(default=False)),
                ('description', models.TextField()),
                ('fork', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
                ('pushed_at', models.DateTimeField()),
                ('homepage', models.TextField()),
                ('size', models.IntegerField()),
                ('stargazers_count', models.IntegerField()),
                ('watchers_count', models.IntegerField()),
                ('has_issues', models.BooleanField(default=False)),
                ('has_downloads', models.BooleanField(default=False)),
                ('has_wiki', models.BooleanField(default=False)),
                ('has_pages', models.BooleanField(default=False)),
                ('forks_count', models.IntegerField()),
                ('open_issues_count', models.IntegerField()),
                ('default_branch', models.CharField(max_length=200)),
                ('network_count', models.IntegerField()),
                ('subscribers_count', models.IntegerField()),
                ('commits_count', models.IntegerField()),
                ('branches_count', models.IntegerField()),
                ('releases_count', models.IntegerField()),
                ('contributors_count', models.IntegerField()),
                ('language', models.ForeignKey(to='crawler.Language', null=True)),
                ('latest_attempt', models.ForeignKey(to='crawler.Attempt', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('name', models.CharField(max_length=200, serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='repository',
            name='repo_type',
            field=models.ForeignKey(to='crawler.Type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='package',
            name='package_type',
            field=models.ForeignKey(to='crawler.Type'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together=set([('package_type', 'name', 'version')]),
        ),
        migrations.AddField(
            model_name='module',
            name='package',
            field=models.ForeignKey(to='crawler.Package'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='module',
            unique_together=set([('name', 'package')]),
        ),
        migrations.AddField(
            model_name='dependency',
            name='package',
            field=models.ForeignKey(to='crawler.Package'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dependency',
            name='source',
            field=models.ForeignKey(to='crawler.Source'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dependency',
            unique_together=set([('attempt', 'package')]),
        ),
        migrations.AddField(
            model_name='commit',
            name='database',
            field=models.ForeignKey(to='crawler.Database', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commit',
            name='repo',
            field=models.ForeignKey(to='crawler.Repository'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='commit',
            unique_together=set([('repo', 'sha')]),
        ),
        migrations.AddField(
            model_name='attempt',
            name='commit',
            field=models.ForeignKey(to='crawler.Commit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attempt',
            name='dependencies',
            field=models.ManyToManyField(to='crawler.Package', through='crawler.Dependency'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attempt',
            name='result',
            field=models.ForeignKey(to='crawler.Result'),
            preserve_default=True,
        ),
    ]
