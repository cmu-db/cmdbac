from django.db import models

# Create your models here.

class Repository(models.Model):
    full_name = models.CharField(max_length=200, primary_key=True)
    repo_type = models.ForeignKey('Type')

class Result(models.Model):
    result = models.CharField(max_length = 200, primary_key=True)

class Attempt(models.Model):
    time = models.DateTimeField()
    repo = models.ForeignKey('Repository')
    result = models.ForeignKey('Result')
    log = models.TextField()

class Status(models.Model):
    status = models.CharField(max_length = 200, primary_key=True)

class Type(models.Model):
    repo_type = models.CharField(max_length = 200, primary_key=True)

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
    source = models.CharField(max_length=200, primary_key=True)

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
    
