from django.shortcuts import render
from models import *
from forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

class Statistic:
    def __init__(self, repo_type, num_repo, num_pkg, num_suc, num_deploy):
        self.repo_type = repo_type
        self.num_repo = num_repo
        self.num_pkg = num_pkg
        self.num_suc = num_suc
        self.num_deploy = num_deploy

def home(request):
    context = {}
    stats = []
    for t in Type.objects.all():
        repo_type = t.name
        repos = Repository.objects.filter(repo_type=t)
        num_repo = repos.count()
        num_suc = repos.filter(last_attempt__result__name="Success").count()
        num_pkg = Package.objects.filter(package_type=t).count()
        num_deploy = repos.exclude(last_attempt=None).count
        stat = Statistic(repo_type, num_repo, num_pkg, num_suc, num_deploy)
        stats.append(stat)
    context['stats'] = stats
    context['attempts'] = Attempt.objects.order_by('-time')[:5]
    return render(request, 'crawler/index.html', context)

def repositories(request):
    print request.GET
    print request.GET
    context = {}
    context['queries'] = request.GET.copy()
    queries_no_page = request.GET.copy()
    if queries_no_page.__contains__('page'):
        del queries_no_page['page']
    context['queries_no_page'] = queries_no_page
    queries_no_page_order = queries_no_page.copy() 
    if queries_no_page_order.__contains__('order_by'):
        context['order_by'] = request.GET.get('order_by')
        del queries_no_page_order['order_by']
    context['queries_no_page_order'] = queries_no_page_order

    repositories = Repository.objects.all()
    if request.GET.__contains__('search'):
        repositories = repositories.filter(full_name__contains=request.GET['search'])
        context
    result_list = request.GET.getlist('results')
    if result_list:
        repositories = repositories.filter(last_attempt__result__name__in=result_list)
    type_list = request.GET.getlist('types')
    if type_list:
        print type(request.GET['types'])
        repositories = repositories.filter(repo_type__name__in=type_list)
    order_by = request.GET.get('order_by', 'full_name')
    repositories = repositories.order_by(order_by)

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
    search = request.GET.get('search', '')
    context["result_form"] = ResultForm(request.GET)
    context['type_form'] = TypeForm(request.GET)
    context["repositories"] = repositories
    context['search'] = search
    print 'search: ' + str(search)
    print queries_no_page
    return render(request, 'crawler/repositories.html', context)

def repository(request, user_name, repo_name):
    context = {}
    context['queries'] = request.GET.copy()
    print 'queries: '
    print request.GET.copy()
    
    repository = Repository.objects.get(full_name=user_name + '/' + repo_name)
    attempts = Attempt.objects.filter(repo=repository)
    context['repository'] = repository
    context['attempts'] = attempts
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

def dependency(request, id):
    dependencies = Dependency.objects.filter(attempt__id=id)
    context = {}
    context['dependencies'] = dependencies
    return render(request, 'crawler/dependency.html', context)

def attempt(request, id):
    attempt = Attempt.objects.get(id=id)
    dependencies = Dependency.objects.filter(attempt__id=id).order_by('package__name')
    context = {}
    context['attempt'] = attempt
    context['dependencies'] = dependencies
    context['queries'] = request.GET.copy()
    return render(request, 'crawler/attempt.html', context)
