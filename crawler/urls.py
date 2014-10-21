from django.conf.urls import patterns, include, url
urlpatterns = patterns('',
    url(r'^$', 'crawler.views.home', name='home'),
    url(r'^dbapps/$', 'crawler.views.dbapps', name='dbapps'),
    url(r'^dps/$', 'crawler.views.dps', name='dps'),
    url(r'^dp/(?P<id>\d+)$', 'crawler.views.modules', name='modules')
)
