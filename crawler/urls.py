from django.conf.urls import patterns, include, url
urlpatterns = patterns('',
    url(r'^$', 'crawler.views.home', name='home'),
    url(r'^statistics/$', 'crawler.views.statistics', name='statistics'),
    url(r'^repositories/$', 'crawler.views.repositories', name='repositories'),
    url(r'^packages/$', 'crawler.views.packages', name='packages'),
    url(r'^repository/(?P<full_name>.*)$', 'crawler.views.repository', name='repository'),
    url(r'^package/(?P<id>\d+)$', 'crawler.views.package', name='package'),
    url(r'^dependency/(?P<id>\d+)$', 'crawler.views.dependency', name='dependency'),
    url(r'^log/(?P<id>\d+)$', 'crawler.views.log', name='log'),
)
