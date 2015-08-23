#!/usr/bin/env python
import sys
import os
import importlib

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))

def get_urls_rec(urllist, url):
    for entry in urllist:
        new_entry = entry.regex.pattern
        new_url = os.path.join(url, new_entry)
        if hasattr(entry, 'url_patterns'):
            get_urls_rec(entry.url_patterns, new_url)
        else:
            print new_url

def main():
    if len(sys.argv) != 3:
        return
    dirname = sys.argv[1]
    sys.path.append(dirname)
    proj_name = sys.argv[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", proj_name + '.settings')
    try:
# only required in Django 1.7
        import django
        django.setup()
    except:
        pass

    urls_module = importlib.import_module(proj_name + '.urls')
    get_urls_rec(urls_module.urlpatterns, '')

if __name__ == "__main__":
    main()
