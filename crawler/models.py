from django.db import models

#Create your models here.

class Repository(models.Model):
    full_name = models.CharField(max_length=200, primary_key=True)
    repo_type = models.ForeignKey('Type')
    latest_attempt = models.ForeignKey('Attempt', null=True)
    private = models.BooleanField(default=False)
    description = models.TextField()
    fork = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    pushed_at = models.DateTimeField()
    homepage = models.TextField()
    size = models.IntegerField()
    stargazers_count = models.IntegerField()
    watchers_count = models.IntegerField()
    language = models.ForeignKey('Language', null=True)
    has_issues = models.BooleanField(default=False)
    has_downloads = models.BooleanField(default=False)
    has_wiki = models.BooleanField(default=False)
    has_pages = models.BooleanField(default=False)
    forks_count = models.IntegerField()
    open_issues_count = models.IntegerField()
    default_branch = models.CharField(max_length=200)
    network_count = models.IntegerField()
    subscribers_count = models.IntegerField()
    commits_count = models.IntegerField()
    branches_count = models.IntegerField()
    releases_count = models.IntegerField()
    contributors_count = models.IntegerField()
    def get_user_name(self):
        return self.full_name.split('/')[0]
    def get_repo_name(self):
        return self.full_name.split('/')[1]

class Commit(models.Model):
    repo = models.ForeignKey('Repository')
    sha = models.CharField(max_length=200)
    database = models.ForeignKey('Database', null=True)
    class Meta:
        unique_together = ('repo', 'sha')

class Database(models.Model):
    name = models.CharField(max_length=200, primary_key=True)

class Language(models.Model):
    name = models.CharField(max_length=200, primary_key=True)

class Result(models.Model):
    name = models.CharField(max_length=200, primary_key=True)

class Status(models.Model):
    name = models.CharField(max_length = 200, primary_key=True)

class Type(models.Model):
    name = models.CharField(max_length = 200, primary_key=True)

class Package(models.Model):
    package_type = models.ForeignKey('Type')
    name = models.CharField(max_length = 200)
    version = models.CharField(max_length = 200)
    count = models.IntegerField(default=0)
    class Meta:
        unique_together = ('package_type', 'name', 'version')

class Dependency(models.Model):
    attempt = models.ForeignKey('Attempt')
    package = models.ForeignKey('Package')
    source = models.ForeignKey('Source')
    class Meta:
        unique_together = ('attempt', 'package')

class Attempt(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    commit = models.ForeignKey('Commit')
    result = models.ForeignKey('Result')
    log = models.TextField(default='')
    dependencies = models.ManyToManyField(Package, through='Dependency')
    hostname = models.CharField(max_length = 200)

class Source(models.Model):
    name = models.CharField(max_length=200, primary_key=True)

class Module(models.Model):
    name = models.CharField(max_length = 200)
    package = models.ForeignKey('Package')
    class Meta:
        unique_together = ('name', 'package')

class Name(models.Model):
    name = models.CharField(max_length=200)
    module = models.ForeignKey('Module', related_name='+')
    class Meta:
        unique_together = ('name', 'module')
