from django.db import models

#Create your models here.

class Repository(models.Model):
   full_name = models.CharField(max_length=200, primary_key=True)
   repo_type = models.ForeignKey('Type')
   last_attempt = models.ForeignKey('Attempt', null=True)
   private = models.BooleanField()
   description = models.TextField()
   fork = models.BooleanField()
   created_at = models.DateTimeField()
   updated_at = models.DateTimeField()
   pushed_at = models.DateTimeField()
   homepage = models.TextField()
   size = models.IntegerField()
   watchers_count = models.IntegerField()
   language = models.ForeignKey('Language', null=True)
   has_issues = models.BooleanField()
   has_downloads = models.BooleanField()
   has_wiki = models.BooleanField()
   has_pages = models.BooleanField()
   forks_count = models.IntegerField()
   open_issues_count = models.IntegerField()
   default_branch = models.CharField(max_length=200)
   network_count = models.IntegerField()
   subscribers_count = models.IntegerField()


class Language(models.Model):
   name = models.CharField(max_length=200, primary_key=True)

class Result(models.Model):
   name = models.CharField(max_length=200, primary_key=True)

class Attempt(models.Model):
   time = models.DateTimeField()
   repo = models.ForeignKey('Repository')
   result = models.ForeignKey('Result')
   log = models.TextField()

class Status(models.Model):
   name = models.CharField(max_length = 200, primary_key=True)

class Type(models.Model):
   name = models.CharField(max_length = 200, primary_key=True)

class Package(models.Model):
   package_type = models.ForeignKey('Type')
   name = models.CharField(max_length = 200)
   version = models.CharField(max_length = 200)
   #count = models.IntegerField()
   class Meta:
       unique_together = ('package_type', 'name', 'version')

class Dependency(models.Model):
   attempt = models.ForeignKey('Attempt')
   package = models.ForeignKey('Package')
   source = models.ForeignKey('Source')
   class Meta:
       unique_together = ('attempt', 'package')

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
