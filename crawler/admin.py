from django.contrib import admin
from crawler.models import *

class RepositoryAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'full_name', 'repo_type', 'commits_count', 'description', 'crawler_date' ]
    list_filter = ['repo_type', 'crawler_date']
# CLASS

class AttemptAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'repo', 'result_name', 'start_time' ]
    list_filter = ['result', 'start_time']
# CLASS

# Register your models here.
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Database)
admin.site.register(Type)
admin.site.register(Package)
admin.site.register(Dependency)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Module)
