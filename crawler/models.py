from django.db import models

# Dependency Package Source
PACKAGE_SOURCE = (
    ('D', 'Database'),
    ('F', 'File'),
)
for x,y in PACKAGE_SOURCE:
    globals()['PACKAGE_SOURCE_' + y.upper()] = x

# Deployment Attempt Status
ATTEMPT_STATUS = (
    ('DP', 'Deploying', 'info'),
    ('DE', 'Download Error', 'danger'),
    ('DR', 'Duplicate Required Files', 'warning'),
    ('MD', 'Missing Dependencies', 'danger'),
    ('MR', 'Missing Required Files', 'danger'),
    ('NA', 'Not an Application', 'warning'),
    ('RE', 'Running Error', 'danger'),
    ('OK', 'Success', 'success'),
    ('UN', 'Unknown', 'warning'),
)
ATTEMPT_STATUS_CODES = { }
ATTEMPT_STATUS_NAMES = { }
temp = [ ]
for x,y,z in ATTEMPT_STATUS:
    globals()['ATTEMPT_STATUS_' + y.replace(" ", "_").upper()] = x
    ATTEMPT_STATUS_CODES[x] = z
    ATTEMPT_STATUS_NAMES[x] = y
    temp.append( (x,y) )
ATTEMPT_STATUS = temp
globals()['ATTEMPT_STATUS_CODES'] = ATTEMPT_STATUS_CODES

# ----------------------------------------------------------------------------

class ProjectType(models.Model):
    name = models.CharField(max_length=16)
    filename = models.CharField(max_length=200)
    min_size = models.IntegerField()
    max_size = models.IntegerField()
    cur_size = models.IntegerField()
    
    def __unicode__(self):
        return self.name
# CLASS

class RepositorySource(models.Model):
    name = models.CharField(max_length=16)
    baseurl = models.CharField(max_length=200)
    crawler_class = models.CharField(max_length=16)
    search_token = models.CharField(max_length=128, null=True)
    last_crawler_time = models.DateTimeField()
    
    def __unicode__(self):
        return self.name
# CLASS

class Database(models.Model):
    name = models.CharField(max_length=16)

    def __unicode__(self):
        return self.name
## CLASS

class Repository(models.Model):
    full_name = models.CharField(max_length=200, null=False, unique=True)
    project_type = models.ForeignKey('ProjectType')
    source = models.ForeignKey('RepositorySource')
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
    language = models.CharField(max_length=200)
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
    attempts_count = models.IntegerField()
    crawler_date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.full_name
    def get_user_name(self):
        return self.full_name.split('/')[0]
    def get_repo_name(self):
        return self.full_name.split('/')[1]
## CLASS

class Package(models.Model):
    project_type = models.ForeignKey('ProjectType')
    name = models.CharField(max_length = 200)
    version = models.CharField(max_length = 200)
    count = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together = ('project_type', 'name', 'version')
        
# CLASS

class Dependency(models.Model):
    attempt = models.ForeignKey('Attempt')
    package = models.ForeignKey('Package')
    source = models.CharField(max_length=2, choices=PACKAGE_SOURCE, default=None, null=True)
    class Meta:
        unique_together = ('attempt', 'package')
# CLASS

class Attempt(models.Model):
    def resultLabel(self):
        return ATTEMPT_STATUS_CODES[self.result]
    def resultName(self):
        return ATTEMPT_STATUS_NAMES[self.result]
    def duration(self):
        return (self.stop_time - self.start_time).total_seconds()
    
    start_time = models.DateTimeField()
    stop_time = models.DateTimeField(default=None, null=True)
    duration = property(duration)
    result = models.CharField(max_length=2, choices=ATTEMPT_STATUS, default=None, null=True)
    result_label = property(resultLabel)
    result_name = property(resultName)
    log = models.TextField(default='')
    dependencies = models.ManyToManyField(Package, through='Dependency')
    hostname = models.CharField(max_length=200)
    sha = models.CharField(max_length=200, null=True)
    database = models.ForeignKey('Database', null=False)
    repo = models.ForeignKey('Repository', null=True)
    base_dir = models.CharField(max_length=200, null=True)
    setting_dir = models.CharField(max_length=200, null=True)
# CLASS

class Module(models.Model):
    name = models.CharField(max_length = 200)
    package = models.ForeignKey('Package')
    class Meta:
        unique_together = ('name', 'package')
# CLASS

