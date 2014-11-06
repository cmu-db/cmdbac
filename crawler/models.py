from django.db import models

# Create your models here.
class User(models.Model):
    id = models.IntegerField(primary_key=True)
    login = models.CharField(max_length=200)
    http_url = models.CharField(max_length=200)

class Repository(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)
    owner = models.ForeignKey('User')
    num_tables = models.IntegerField()
    #pushed_at = models.DateTimeField()
    http_url = models.CharField(max_length=200)
    download_url = models.CharField(max_length=200)
    #requirements_path = models.CharField(max_length = 100, blank=True)
    #manage_path = models.CharField(max_length = 100, blank=True)
    #settings_path = models.CharField(max_length = 100, blank=True)
    #models_path = models.CharField(max_length=100, blank=True)
    #model_size = models.IntegerField(blank=True, null=True)
    app_type = models.ForeignKey('Type')
    #status = models.ForeignKey('Status')
    #result = models.ForeignKey('Result', blank=True, null=True)

    #class Meta:
    #    unique_together = ('repo_id', 'pushed_at')

class Result(models.Model):
    result = models.CharField(max_length = 200, primary_key=True)

class Attempt(models.Model):
    app = models.ForeignKey('Repository')
    result = models.ForeignKey('Result')
    log = models.TextField()

class Status(models.Model):
    status = models.CharField(max_length = 200, primary_key=True)

class Type(models.Model):
    app_type = models.CharField(max_length = 200, primary_key=True)


#class Library:
#    repo_id = models.IntegerField()
#    pushed_at = models.DateTimeField()
#    url = models.CharField(max_length = 160)
#    setup_path = models.CharField(max_length = 100)
#
#    class Meta:
#        unique_together = ('repo_id', 'pushed_at')

class Package(models.Model):
    package_type = models.ForeignKey('Type')
    name = models.CharField(max_length = 200)
    version = models.CharField(max_length = 200)
    #count = models.IntegerField()
    class Meta:
        unique_together = ('package_type', 'name', 'version')

class Dependency(models.Model):
    app = models.ForeignKey('Repository')
    package = models.ForeignKey('Package')
    class Meta:
        unique_together = ('app', 'package')

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
    
