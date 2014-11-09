from django.shortcuts import render
from models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

def home(request):
    return render(request, 'crawler/index.html', {})

class Statistic:
    def __init__(self, repo_type, num_repo, num_pkg):
        self.repo_type = repo_type
        self.num_repo = num_repo
        self.num_pkg = num_pkg

def statistics(request):
    context = {}
    types = Type.objects.all()
    stats = []
    for t in types:
        repo_type = t.repo_type
        num_repo = Repository.objects.filter(repo_type=t).count()
        num_pkg = Package.objects.filter(package_type=t).count()
        stat = Statistic(repo_type, num_repo, num_pkg)
        stats.append(stat)
    context['stats'] = stats
    return render(request, 'crawler/statistics.html', context)

def repositories(request):
    repositories = Repository.objects.all().order_by('full_name')
    paginator = Paginator(repositories, 100) # Show 100 contacts per page
    page = request.GET.get('page')
    try:
        repositories = paginator.page(page)
    except PageNotAnInteger:
# If page is not an integer, deliver first page.
        repositories = paginator.page(1)
    except EmptyPage:
# If page is out of range (e.g. 9999), deliver last page of results.
        repositories = paginator.page(paginator.num_pages)
    context = {"repositories": repositories}
    return render(request, 'crawler/repositories.html', context)

def repository(request, full_name):
    repository = Repository.objects.all().get(full_name=full_name)
    attemps = Attempt.objects.all().filter(repo=repository)
    context = {}
    context['repository'] = repository
    context['attemps'] = attemps
    return render(request, 'crawler/repository.html', context)

def packages(request):
    packages = Package.objects.all().order_by('name', 'version')
    paginator = Paginator(packages, 100) # Show 100 contacts per page
    page = request.GET.get('page')
    try:
        packages = paginator.page(page)
    except PageNotAnInteger:
# If page is not an integer, deliver first page.
        packages = paginator.page(1)
    except EmptyPage:
# If page is out of range (e.g. 9999), deliver last page of results.
        packages = paginator.page(paginator.num_pages)
    context = {'packages': packages}
    return render(request, 'crawler/packages.html', context)
     
def package(request, id):
    package = Package.objects.get(id=id)
    modules = Module.objects.filter(package__id=id)
    context = {}
    context['package'] = package
    context['modules'] = modules
    return render(request, 'crawler/package.html', context)
