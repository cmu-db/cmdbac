from django.conf import settings
from django.db import models


STATES = settings.PINAX_BLOG_UNPUBLISHED_STATES + ["Published"]
PINAX_BLOG_STATE_CHOICES = list(zip(list(range(1, 1 + len(STATES))), STATES))
PUBLISHED_STATE = len(settings.PINAX_BLOG_UNPUBLISHED_STATES) + 1


class PostManager(models.Manager):

    def published(self):
        return self.filter(published__isnull=False, state=PUBLISHED_STATE)

    def current(self):
    	return self.published().order_by("-published")
