from django.db import models

# Create your models here.
class Repository(models.Model):
    repo_id = models.IntegerField()
    pushed_at = models.DateTimeField()
    url = models.CharField(max_length=160)

    class Meta:
        unique_together = ("repo_id", "pushed_at")

#class User(models.Model):
#    id = models.IntegerField(primary_key=True)
#    login = models.CharField(max_length=40)
