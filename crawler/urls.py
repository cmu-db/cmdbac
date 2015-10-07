from django.conf.urls import patterns, include, url
urlpatterns = patterns('',
    url(r'^$', 'crawler.views.home', name='home'),
    url(r'^repositories/$', 'crawler.views.repositories', name='repositories'),
    url(r'^repository/(?P<user_name>.+)/(?P<repo_name>.+)/', 'crawler.views.repository', name='repository'),
    url(r'^attempt/(?P<id>\d+)/', 'crawler.views.attempt', name='attempt'),
    #url(r'^search/$', 'crawler.views.search', name='search'),
)
