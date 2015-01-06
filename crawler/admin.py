from django.contrib import admin
from crawler.models import *

class DependencyInline(admin.StackedInline):
    model = Dependency
    extra = 3

class RepositorySourceAdmin(admin.ModelAdmin):
    list_display = [ 'name', 'baseurl', 'crawler_class', 'search_token', 'last_crawler_time' ]
## CLASS

class RepositoryAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'name', 'get_project_type', 'source', 'commits_count', 'description', 'crawler_date' ]
    list_filter = ['project_type', 'crawler_date']
    fieldsets = [
        (None,               {'fields': ['name', 'project_type', 'source', 'description']}),
        ('Date information', {'fields': ['created_at', 'updated_at', 'pushed_at']}),
    ]
    
    def get_project_type(self, obj):
        return obj.project_type.name

    get_project_type.short_description = 'Project Type'

    
# CLASS

class AttemptAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'repo', 'result_name', 'start_time', 'stop_time' ]
    list_filter = ['result', 'start_time']
    #inlines = [DependencyInline]
# CLASS

class PackageAdmin(admin.ModelAdmin):
    list_display = [ 'name', 'project_type', 'version', 'count' ]
    list_filter = ['project_type']
# CLASS

# Register your models here.
admin.site.register(RepositorySource, RepositorySourceAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Database)
admin.site.register(ProjectType)
admin.site.register(Package, PackageAdmin)
admin.site.register(Dependency)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Module)
