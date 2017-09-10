import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import traceback
import markdown
import math
from threading import Thread
from multiprocessing import Process
import time

from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response
from serializers import AttemptSerializer, RepositorySerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count
from django.db.models import Max
from django.http import StreamingHttpResponse
from django.db.models.query import QuerySet
from models import *
from forms import *
import utils

class MainPageStatistic:
    def __init__(self, project_type, last_updated, num_repo, num_suc, num_deploy, num_valid_deploy):
        self.project_type = project_type
        self.last_updated = last_updated
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
    total_success = 0
    for t in ProjectType.objects.all():
        repo_type = t.name
        repos = Repository.objects.filter(project_type=t)

        # Total number of repositories for this project type
        num_repo = repos.count()

        # Total number of succesful attempts for this project type
        num_suc = repos.exclude(latest_successful_attempt=None).count()
        total_success += num_suc

        # The timestamp of the last attempt (doesn't have to be succesful)
        last_updated = repos.aggregate(Max('updated_date'))
        if type(last_updated) is dict:
            last_updated = last_updated.values()[0]

        # num_pkg = Package.objects.filter(project_type=t).count()
        num_deploy = repos.exclude(latest_attempt=None).count()
        num_valid_deploy = repos.filter(valid_project=True).count()
        stat = MainPageStatistic(t, last_updated, num_repo, num_suc, num_deploy, num_valid_deploy)
        stats.append(stat)
    ## FOR

    context['stats'] = stats

    # Round down to the nearest thousand
    context['total_success'] = int(math.floor(total_success/1000.0) * 1000)

    context['attempts'] = Attempt.objects.filter(result=ATTEMPT_STATUS_SUCCESS).order_by('-start_time')[:5]
    return render(request, 'index.html', context)
## DEF

def super_user_stuff(request):
    pass
## DEF

def search_stuff(context, request):
    if len(request) == 0:
        request.setlist('results', [ATTEMPT_STATUS_SUCCESS])
        request.setlist('types', ProjectType.objects.all().values_list('name', flat=True))

    repositories = Repository.objects.all()

    if request.get('search', '') != '':
        repo_name = request['search']
        print 'search: ' + repo_name
        context['search'] = repo_name
        repositories = repositories.filter(name__contains=repo_name)

    result_list = request.getlist('results')
    if result_list:
        repositories = repositories.filter(latest_attempt__result__in=result_list)

    type_list = request.getlist('types')
    if type_list:
        repositories = repositories.filter(project_type__name__in=type_list)

    if len(result_list) == 1 and result_list[0] == ATTEMPT_STATUS_SUCCESS:
        for description in StatisticsForm(request).fields:
            try:
                if description in request:
                    bounds = request.get(description).split('-')
                    lower_bound = int(bounds[0])
                    upper_bound = int(bounds[1])
                else:
                    lower_bound = 0
                    upper_bound = 0
            except:
                lower_bound = 0
                upper_bound = 0
            if lower_bound > 0 or upper_bound > 0:
                attempts = Statistic.objects.filter(description = description).filter(count__gte=lower_bound).filter(count__lte=upper_bound).values_list('attempt', flat = True)
                repositories = repositories.filter(latest_attempt__in = attempts)

    return repositories

def repositories(request):
    context = {}
    context['queries'] = request.GET.copy()

    super_user_stuff(request)

    repositories = search_stuff(context, context['queries'])

    queries_no_page = context['queries'].copy()
    if queries_no_page.__contains__('page'):
        del queries_no_page['page']
    if queries_no_page.__contains__('search') and queries_no_page['search'] == '':
        del queries_no_page['search']
    context['queries_no_page'] = queries_no_page

    queries_no_page_order = queries_no_page.copy()
    if queries_no_page_order.__contains__('order_by'):
        context['order_by'] = context['queries'].get('order_by')
        del queries_no_page_order['order_by']
    context['queries_no_page_order'] = queries_no_page_order

    context["result_form"] = ResultForm(context['queries'])
    context['type_form'] = ProjectTypeForm(context['queries'])
    context["statistics_form"] = StatisticsForm(context['queries'])

    order_by = context['queries'].get('order_by', 'crawler_date')
    repositories = repositories.order_by(order_by)

    paginator = Paginator(repositories, 50) # Show 50 repos per page
    page = context['queries'].get('page')
    try:
        repositories = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        repositories = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        repositories = paginator.page(paginator.num_pages)

    context["repositories"] = repositories

    return render(request, 'repositories.html', context)

def repository(request, user_name, repo_name):
    context = {}
    context['queries'] = request.GET.copy()

    repository = Repository.objects.get(name=user_name + '/' + repo_name)
    context['repository'] = repository

    attempts = Attempt.objects.filter(repo=repository).order_by("-id")
    paginator = Paginator(attempts, 50) # Show 50 repos per page
    page = request.GET.get('page')
    try:
        attempts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        attempts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        attempts = paginator.page(paginator.num_pages)
    context['attempts'] = attempts

    return render(request, 'repository.html', context)

def attempt(request, id):
    context = {}

    context['queries'] = request.GET.copy()

    attempt = Attempt.objects.get(id=id)
    context['attempt'] = attempt

    dependencies = Dependency.objects.filter(attempt__id=id).order_by('package__name')
    context['dependencies'] = dependencies

    keyword_order = {
        'SELECT': 1,
        'INSERT': 2,
        'UPDATE': 3,
        'DELETE': 4
    }

    context['statistics'] = {}
    for statistic in Statistic.objects.filter(attempt=attempt):
        context['statistics'][statistic.description] = max(statistic.count, context['statistics'].get(statistic.description, 0))

    actions = Action.objects.filter(attempt=attempt)
    context['actions'] = []
    for action in actions:
        fields = Field.objects.filter(action=action)
        counters = Counter.objects.filter(action=action)
        counters = sorted(counters, key = lambda x: keyword_order.get(x.description, 10))
        context['actions'].append({
            'id': action.id,
            'url': action.url,
            'method': action.method,
            'fields': fields,
            'counters': counters
        })

    try:
        image = Image.objects.get(attempt=attempt)
        screenshot_filename = 'screenshot_{}.png'.format(attempt.id)
        utils.mk_dir(os.path.join(os.path.dirname(__file__), 'static', 'screenshots'))
        screenshot = open(os.path.join(os.path.dirname(__file__), 'static', 'screenshots', screenshot_filename), 'wb')
        screenshot.write(image.data)
        screenshot.close()
        context['screenshot'] = '/static/screenshots/' + screenshot_filename
    except:
        traceback.print_exc()

    return render(request, 'attempt.html', context)

def queries(request, id):
    if request.is_ajax():
        context = {}

        action = Action.objects.get(id=id)
        queries = Query.objects.filter(action=action)
        context['queries'] = queries

        return render(request, 'queries.html', context)

def about(request):
    return render(request, 'about.html')

def search(request):
    context = {}
    context["result_form"] = ResultForm(request.GET)
    context['type_form'] = ProjectTypeForm(request.GET)
    context["statistics_form"] = StatisticsForm(request.GET)

    return render(request, 'search.html', context)

class AttemptViewSet(viewsets.ViewSet):
    def get_queryset(self):
        return Attempt.objects.all()

    @detail_route(methods=['get'])
    def info(self, request, pk):
        queryset = Attempt.objects.all()
        attempt = get_object_or_404(queryset, id=pk)
        serializer = AttemptSerializer(attempt)
        web_statistic = WebStatistic.objects.get(name = 'Attempt Info API')
        web_statistic.count += 1
        web_statistic.save()
        attempt_info_count, _ = Statistic.objects.get_or_create(description = 'Attempt Info API', attempt = attempt)
        attempt_info_count.count += 1
        attempt_info_count.save()
        return Response(serializer.data)

class RepositoryViewSet(viewsets.ViewSet):
    def get_queryset(self):
        return Repository.objects.all()

    @detail_route(methods=['get'])
    def info(self, request, pk):
        queryset = Repository.objects.all()
        repo = get_object_or_404(queryset, id=pk)
        serializer = RepositorySerializer(repo)
        return Response(serializer.data)

class RepositoryListView(generics.ListAPIView):
    queryset = Repository.objects.filter(valid_project=True)
    serializer_class = RepositorySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('project_type', 'source')
