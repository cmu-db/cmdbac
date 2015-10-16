import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import traceback
from threading import Thread
 
from django.shortcuts import render
from models import *
from forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Count

import utils
import crawlers

class Statistic:
    def __init__(self, repo_type, num_repo, num_suc, num_deploy, num_valid_deploy):
        self.repo_type = repo_type
        self.num_repo = num_repo
        self.num_suc = num_suc
        self.num_deploy = num_deploy
        self.num_valid_deploy = num_valid_deploy
        if self.num_valid_deploy == 0:
            self.suc_rate = 0
        else:
            self.suc_rate = int(self.num_suc * 100 / self.num_valid_deploy)

def home(request):
    context = {}
    stats = []
    for t in ProjectType.objects.all():
        repo_type = t.name
        repos = Repository.objects.filter(project_type=t)
        num_repo = repos.count()
        num_suc = repos.filter(latest_attempt__result=ATTEMPT_STATUS_SUCCESS).count()
        # num_pkg = Package.objects.filter(project_type=t).count()
        num_deploy = repos.exclude(latest_attempt=None).count()
        num_valid_deploy = repos.filter(valid_project=True).count()
        stat = Statistic(repo_type, num_repo, num_suc, num_deploy, num_valid_deploy)
        stats.append(stat)
    context['stats'] = stats
    context['attempts'] = Attempt.objects.exclude(result=ATTEMPT_STATUS_MISSING_REQUIRED_FILES).order_by('-start_time')[:5]
    return render(request, 'index.html', context)

def repositories(request):
    #print request.GET
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

    # repositories = Repository.objects.filter(valid_project=True)

    if request.user.is_superuser:
        if request.GET.__contains__('module') and request.GET.__contains__('package') and request.GET.__contains__('type') and request.GET.__contains__('version'):
            module_name = request.GET['module']
            package_name = request.GET['package']
            package_type = request.GET['type']
            package_version = request.GET['version']
            print 'add ' + package_type + ' module : ' + module_name
            project_type_map = {'django': 1, 'ror': 2}
            try:    
                utils.add_module(module_name, package_name, project_type_map[package_type], package_version)
                messages.success(request, 'Successfully added new module {}'.format(module_name))
            except:
                messages.error(request, 'Failed to add new module {}'.format(repo_name))
                traceback.print_exc()
            finally:
                return redirect('repositories')

        if request.GET.__contains__('repo') and request.GET.__contains__('type'):
            repo_name = request.GET['repo']
            repo_type = request.GET['type']
            repo_setup_scripts = request.GET['scripts']
            print 'add ' + repo_type + ' repository : ' + repo_name
            project_type_map = {'django': 1, 'ror': 2}
            try:    
                utils.add_repo(repo_name, project_type_map[repo_type], repo_setup_scripts)
                messages.success(request, 'Successfully added new repository {}'.format(repo_name))
            except:
                messages.error(request, 'Failed to add new repository {}'.format(repo_name))
                traceback.print_exc()
            finally:
                return redirect('repositories')

        if request.GET.__contains__('deploy'):
            repo_name = request.GET['deploy']
            print 'deploy: ' + repo_name
            try:
                thread = Thread(target = utils.deploy_repo, args = (repo_name, ))
                thread.start()
                # thread.join()
                messages.success(request, 'Deploying repository {}'.format(repo_name))
            except:
                messages.error(request, 'Failed to deploy repository {}'.format(repo_name))
                traceback.print_exc()
            finally:
                return redirect('repositories')

        if request.GET.__contains__('delete'):
            repo_name = request.GET['delete']
            print 'delete: ' + repo_name
            try:
                utils.delete_repo(repo_name)
                messages.success(request, 'Successfully deleted repository {}'.format(repo_name))
            except:
                messages.error(request, 'Failed to delete repository {}'.format(repo_name))
                traceback.print_exc()
            finally:
                return redirect('repositories')

    repositories = Repository.objects.all()
    if request.GET.__contains__('search'):
        repo_name = request.GET['search']
        print 'search: ' + repo_name
        repositories = repositories.filter(name__contains=repo_name)

    result_list = request.GET.getlist('results')
    if result_list:
        repositories = repositories.filter(latest_attempt__result__in=result_list)
    type_list = request.GET.getlist('types')
    if type_list:
        repositories = repositories.filter(project_type__name__in=type_list)
    order_by = request.GET.get('order_by', 'crawler_date')
    if 'attempts_count' in order_by:
        repositories.annotate(attempts_count=Count('attempt')).order_by(order_by)
    elif 'forms_count' in order_by:
        repositories.annotate(forms_count=Count('latest_attempt__form')).order_by(order_by)
    elif 'queries_count' in order_by:
        repositories.annotate(queries_count=Count('latest_attempt__form__query')).order_by(order_by)
    else:
        repositories = repositories.order_by(order_by)

    paginator = Paginator(repositories, 50) # Show 50 repos per page
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
    context['type_form'] = ProjectTypeForm(request.GET)
    context["repositories"] = repositories
    context['search'] = search
    return render(request, 'repositories.html', context)

def repository(request, user_name, repo_name):
    context = {}
    context['queries'] = request.GET.copy()
    
    repository = Repository.objects.get(name=user_name + '/' + repo_name)
    attempts = Attempt.objects.filter(repo=repository).order_by("-id")
    context['repository'] = repository
    context['attempts'] = attempts
    return render(request, 'repository.html', context)

def attempt(request, id):
    context = {}
    context['queries'] = request.GET.copy()

    attempt = Attempt.objects.get(id=id)
    context['attempt'] = attempt

    dependencies = Dependency.objects.filter(attempt__id=id).order_by('package__name')
    context['dependencies'] = dependencies
    
    forms = Form.objects.filter(attempt=attempt)
    context['forms'] = []
    for form in forms:
        fields = Field.objects.filter(form=form)
        queries = Query.objects.filter(form=form)
        context['forms'].append({
            'id': form.id,
            'action': form.action,
            'url': form.url,
            'fields': fields,
            'queries': queries
        })

    try:
        image = Image.objects.get(attempt=attempt)
        screenshot = open(os.path.join(os.path.dirname(__file__), 'static', 'screenshot.png'), 'wb')
        screenshot.write(image.data)
        screenshot.close()
    except:
        pass

    return render(request, 'attempt.html', context)
