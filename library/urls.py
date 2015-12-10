from django.conf.urls import patterns, include, url
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'attempt', views.AttemptViewSet, base_name='attempt')

urlpatterns = patterns('',
	url(r'^api/', include(router.urls)),
    url(r'^$', 'library.views.home', name='home'),
    url(r'^repositories/$', 'library.views.repositories', name='repositories'),
    url(r'^repository/(?P<user_name>.+)/(?P<repo_name>.+)/', 'library.views.repository', name='repository'),
    url(r'^attempt/(?P<id>\d+)/', 'library.views.attempt', name='attempt'),
    url(r'^queries/(?P<id>\d+)/', 'library.views.queries', name='queries'),
    url(r'^about/$', 'library.views.about', name='about'),
    url(r'^tools/$', 'library.views.tools', name='tools'),
    url(r'^search/$', 'library.views.search', name='search')
)
