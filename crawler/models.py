import os
import hurry.filesize
import base64
from django.db import models

# Dependency Package Source
PACKAGE_SOURCE = (
    ('D', 'Database', 'default'),
    ('F', 'File', 'info'),
)
PACKAGE_SOURCE_CODES = {}
PACKAGE_SOURCE_NAMES = {}
temp = []
for x, y, z in PACKAGE_SOURCE:
    globals()['PACKAGE_SOURCE_' + y.upper()] = x
    PACKAGE_SOURCE_CODES[x] = z
    PACKAGE_SOURCE_NAMES[x] = y
    temp.append((x,y))
PACKAGE_SOURCE = temp
globals()['PACKAGE_SOURCE_CODES'] = PACKAGE_SOURCE_CODES

# Deployment Attempt Status
ATTEMPT_STATUS = (
    ('DP', 'Deploying', 'info'),
    ('DE', 'Download Error', 'danger'),
    ('MD', 'Missing Dependencies', 'danger'),
    ('MR', 'Missing Required Files', 'danger'),
    ('RE', 'Running Error', 'danger'),
    ('OK', 'Success', 'success')
)
ATTEMPT_STATUS_CODES = {}
ATTEMPT_STATUS_NAMES = {}
temp = []
for x, y, z in ATTEMPT_STATUS:
    globals()['ATTEMPT_STATUS_' + y.replace(" ", "_").upper()] = x
    ATTEMPT_STATUS_CODES[x] = z
    ATTEMPT_STATUS_NAMES[x] = y
    temp.append((x,y))
ATTEMPT_STATUS = temp
globals()['ATTEMPT_STATUS_CODES'] = ATTEMPT_STATUS_CODES

# Login or Regsiter Status
USER_STATUS = (
    ('OK', 'Success', 'success'),
    ('ER', 'Fail', 'danger'),
    ('NF', 'Not found', 'warning'),
    ('UN', 'Unknown', 'default'),
)
USER_STATUS_CODES = {}
USER_STATUS_NAMES = {}
temp = []
for x, y, z in USER_STATUS:
    globals()['USER_STATUS_' + y.replace(" ", "_").upper()] = x
    USER_STATUS_CODES[x] = z
    USER_STATUS_NAMES[x] = y
    temp.append((x,y))
USER_STATUS = temp
globals()['USER_STATUS_CODES'] = USER_STATUS_CODES

# Benchmark Status
BENCHMARK_STATUS = (
    ('RI', 'Running', 'info'),
    ('DE', 'Download Error', 'danger'),
    ('MD', 'Missing Dependencies', 'danger'),
    ('MR', 'Missing Required Files', 'danger'),
    ('RE', 'Running Error', 'danger'),
    ('OK', 'Success', 'success')
)
BENCHMARK_STATUS_CODES = {}
BENCHMARK_STATUS_NAMES = {}
temp = []
for x, y, z in BENCHMARK_STATUS:
    globals()['BENCHMARK_STATUS_' + y.replace(" ", "_").upper()] = x
    BENCHMARK_STATUS_CODES[x] = z
    BENCHMARK_STATUS_NAMES[x] = y
    temp.append((x,y))
BENCHMARK_STATUS = temp
globals()['BENCHMARK_STATUS_CODES'] = BENCHMARK_STATUS_CODES

# ----------------------------------------------------------------------------

class ProjectType(models.Model):
    name = models.CharField(max_length=16)
    filename = models.CharField(max_length=200)
    deployer_class = models.CharField(max_length=16)
    default_port = models.PositiveSmallIntegerField(null=False)
    logo = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name
## CLASS

class RepositorySource(models.Model):
    name = models.CharField(max_length=16)
    base_url = models.CharField(max_length=200)
    commit_url = models.CharField(max_length=200)
    crawler_class = models.CharField(max_length=16)
    search_token = models.CharField(max_length=128, null=True)
    logo = models.CharField(max_length=100)
    
    def get_url(self, repo_name):
        from string import Template
        t = Template(self.base_url)
        args = {
            "repo_name": repo_name,
        }
        return t.substitute(args)
    ## DEF
    
    def get_commit_url(self, repo_name, commit):
        from string import Template
        t = Template(self.commit_url)
        args = {
            "base_url": self.base_url,
            "repo_name": repo_name,
            "commit": commit,
        }
        return t.substitute(args)
    ## DEF
    
    def __unicode__(self):
        return self.name
## CLASS

class CrawlerStatus(models.Model):
    source = models.ForeignKey('RepositorySource')
    project_type = models.ForeignKey('ProjectType')
    min_size = models.IntegerField()
    cur_size = models.IntegerField()
    max_size = models.IntegerField()
    next_url = models.URLField(null=True)
    query = models.CharField(max_length=128, null=True)
    last_crawler_time = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('source', 'project_type')
        verbose_name_plural = "crawlers"
        
    def __unicode__(self):
        return "Crawler::%s::%s" % (self.source.name, self.project_type.name)
## CLASS

class Database(models.Model):
    name = models.CharField(max_length=16)

    def __unicode__(self):
        return self.name
## CLASS

class Repository(models.Model):
    name = models.CharField(max_length=128, null=False, unique=True)
    project_type = models.ForeignKey('ProjectType')
    source = models.ForeignKey('RepositorySource')
    latest_attempt = models.ForeignKey('Attempt', null=True)
    valid_project = models.NullBooleanField(default=None)
    crawler_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    setup_scripts = models.TextField(null=True)

    private = models.BooleanField(default=False)
    description = models.TextField(null=True)
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

    attempts_count = models.IntegerField(default = 0)

    def __unicode__(self):
        return self.name
    def user_name(self):
        return self.name.split('/')[0]
    def repo_name(self):
        return self.name.split('/')[1]
    def repo_url(self):
        return self.source.get_url(self.name)

    class Meta:
        verbose_name_plural = "repositories"
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
        
## CLASS

class Dependency(models.Model):
    def sourceLabel(self):
        return PACKAGE_SOURCE_CODES[self.source]
    def sourceName(self):
        return PACKAGE_SOURCE_NAMES[self.source]

    attempt = models.ForeignKey('Attempt')
    package = models.ForeignKey('Package')
    source = models.CharField(max_length=2, choices=PACKAGE_SOURCE, default=None, null=True)
    source_label = property(sourceLabel)
    source_name = property(sourceName)

    class Meta:
        unique_together = ('attempt', 'package')
        verbose_name_plural = "dependencies"
## CLASS

class Attempt(models.Model):
    def resultLabel(self):
        return ATTEMPT_STATUS_CODES[self.result]
    def resultName(self):
        return ATTEMPT_STATUS_NAMES[self.result]
    def registerLabel(self):
        return USER_STATUS_CODES[self.register]
    def registerName(self):
        return USER_STATUS_NAMES[self.register]
    def loginLabel(self):
        return USER_STATUS_CODES[self.login]
    def loginName(self):
        return USER_STATUS_NAMES[self.login]
    def duration(self):
        return (self.stop_time - self.start_time).total_seconds()
    def commit_url(self):
        return self.repo.source.get_commit_url(self.repo.name, self.sha)
    def readable_size(self):
        return hurry.filesize.size(self.size, system=hurry.filesize.alternative)

    start_time = models.DateTimeField()
    stop_time = models.DateTimeField(default=None, null=True)
    duration = property(duration)

    repo = models.ForeignKey('Repository', null=True)
    sha = models.CharField(max_length=200, null=True)
    size = models.IntegerField()
    database = models.ForeignKey('Database', null=False)
    dependencies = models.ManyToManyField(Package, through='Dependency')
    log = models.TextField(default='')
    hostname = models.CharField(max_length=200)

    result = models.CharField(max_length=2, choices=ATTEMPT_STATUS, default=None, null=True)
    result_label = property(resultLabel)
    result_name = property(resultName)
    register = models.CharField(max_length=2, choices=USER_STATUS, default=None, null=True)
    register_label = property(registerLabel)
    register_name = property(registerName)
    login = models.CharField(max_length=2, choices=USER_STATUS, default=None, null=True)
    login_label = property(loginLabel)
    login_name = property(loginName)
    
    runtime = models.ForeignKey('Runtime', default=None)

    forms_count = models.IntegerField(default = 0)
    queries_count = models.IntegerField(default = 0)

    def __unicode__(self):
        return unicode(self.id)
## CLASS

class Module(models.Model):
    name = models.CharField(max_length = 200)
    package = models.ForeignKey('Package')
    class Meta:
        unique_together = ('name', 'package')
## CLASS

class Form(models.Model):
    action = models.CharField(max_length = 200)
    url = models.CharField(max_length = 200)
    admin = models.BooleanField(default=False)
    attempt = models.ForeignKey('Attempt', related_name='forms')
## CLASS

class Field(models.Model):
    name = models.CharField(max_length = 200)
    type = models.CharField(max_length = 200)
    form = models.ForeignKey('Form', related_name='fields')
## CLASS

class Counter(models.Model):
    description = models.CharField(max_length = 200)
    count = models.IntegerField(default = 0)
    form = models.ForeignKey('Form')
## CLASS

class Query(models.Model):
    content = models.TextField()
    matched = models.BooleanField(default=False)
    form = models.ForeignKey('Form', related_name='queries')
## CLASS

class Image(models.Model):
    def set_data(self, data):
        self._data = base64.encodestring(data)
    def get_data(self):
        return base64.decodestring(self._data)

    _data = models.TextField(db_column='data', blank=True)
    data = property(get_data, set_data)
    attempt = models.ForeignKey('Attempt')
## CLASS

class Runtime(models.Model):
    executable = models.CharField(max_length = 200)
    version = models.CharField(max_length = 200)
    class Meta:
        unique_together = ('executable', 'version')
## CLASS