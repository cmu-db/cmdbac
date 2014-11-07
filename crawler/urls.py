from django.conf.urls import patterns, include, url
urlpatterns = patterns('',
    url(r'^$', 'crawler.views.home', name='home'),
    url(r'^statistics/$', 'crawler.views.statistics', name='statistics'),
    url(r'^repositories/$', 'crawler.views.repositories', name='repositories'),
    url(r'^packages/$', 'crawler.views.packages', name='packages'),
    url(r'^repository/(?P<full_name>\w+$', 'crawler.views.repository', name='repository')
    url(r'^dp/(?P<id>\d+)$', 'crawler.views.modules', name='modules')
)
