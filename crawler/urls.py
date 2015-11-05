from django.conf.urls import patterns, include, url
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'attempt', views.AttemptViewSet)

urlpatterns = patterns('',
	url(r'^api/', include(router.urls)),
    url(r'^$', 'crawler.views.home', name='home'),
    url(r'^repositories/$', 'crawler.views.repositories', name='repositories'),
    url(r'^repository/(?P<user_name>.+)/(?P<repo_name>.+)/', 'crawler.views.repository', name='repository'),
    url(r'^attempt/(?P<id>\d+)/', 'crawler.views.attempt', name='attempt'),
    url(r'^queries/(?P<id>\d+)/', 'crawler.views.queries', name='queries'),
    url(r'^about/$', 'crawler.views.about', name='about'),
    #url(r'^search/$', 'crawler.views.search', name='search'),
)
