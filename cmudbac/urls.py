# django imports
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path


urlpatterns = [
    url(r'', include('cmudbac.library.urls')),
    #url(r'^blog/', include('cmudbac.blog.urls')),

    path('admin/', admin.site.urls),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
