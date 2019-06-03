# django imports
from django.conf.urls import include
from django.conf.urls import url
# third-party imports
from rest_framework import routers
# local imports
from . import views


router = routers.DefaultRouter()
router.register(r'attempt', views.AttemptViewSet, base_name='attempt')
router.register(r'repository', views.RepositoryViewSet, base_name='repository')


urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/repositories/', views.RepositoryListView.as_view()),

    url(r'^$', views.home, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^attempt/(?P<id>\d+)/$', views.attempt, name='attempt'),
    url(r'^queries/(?P<id>\d+)/$', views.queries, name='queries'),
    url(r'^repositories/$', views.repositories, name='repositories'),
    url(r'^repository/(?P<user_name>.+)/(?P<repo_name>.+)/$', views.repository, name='repository'),
    url(r'^search/$', views.search, name='search')
]
