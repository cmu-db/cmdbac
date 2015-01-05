from django.contrib import admin
from crawler.models import *

class DependencyInline(admin.StackedInline):
    model = Dependency
    extra = 3

class RepositoryAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'full_name', 'repo_type', 'commits_count', 'description', 'crawler_date' ]
    list_filter = ['repo_type', 'crawler_date']
# CLASS

class AttemptAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'repo', 'result_name', 'start_time', 'stop_time' ]
    list_filter = ['result', 'start_time']
    #inlines = [DependencyInline]
# CLASS

class PackageAdmin(admin.ModelAdmin):
    list_display = [ 'name', 'package_type', 'version', 'count' ]
    list_filter = ['package_type']
# CLASS

# Register your models here.
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Database)
admin.site.register(Type)
admin.site.register(Package, PackageAdmin)
admin.site.register(Dependency)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Module)
