#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2015-11-13 22:02:21
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2015-11-13 22:02:57
from django.conf import settings
from django.template.loader import render_to_string

def analytics(request):
    if settings.DEBUG:
        return ''

    return {
        'analytics_code': render_to_string('analytics/analytics.html', {
            'google_analytics_key': settings.GOOGLE_ANALYTICS_KEY,
        })
    }
