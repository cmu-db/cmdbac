from django.shortcuts import render
from models import *

# Create your views here.
threshold = 5
def home(request):
    apps = Application.objects.all().order_by('pk')
    context = {'apps' : apps}
    context['num_django'] = len(apps)
    context['num_apps'] = Application.objects.filter(app_type=Type.objects.get(app_type='Django: Application')).count()
    context['num_dbapps'] = Application.objects.filter(model_size__gt=threshold, app_type=Type.objects.get(app_type='Django: Application')).count()
    return render(request, 'crawler/index.html', context)


def statistics(request):
    dbapps = Application.objects.filter(model_size__gt=threshold, app_type=Type.objects.get(app_type='Django: Application')).order_by('pk')
    context = {'dbapps': dbapps}
    context['num_dbapps'] = len(dbapps)
    context['num_suc'] = Application.objects.filter(app_type=Type.objects.get(app_type='Django: Application'), model_size__gt=threshold, result=Result.objects.get(result='Success')).count
    context['num_mis'] = Application.objects.filter(app_type=Type.objects.get(app_type='Django: Application'), model_size__gt=threshold, result=Result.objects.get(result='Fail: Missing Dependency')).count
    return render(request, 'crawler/statistics.html', context)

def repositories(request):
    full_names = Repository.objects.values_list('full_name', flat=True).order_by('full_name')
    context = {'full_names': full_names}
    return render(request, 'crawler/repositoreis.html', context)

def repository(request, id):

def dps(request):
    dps = Package.objects.all().order_by('name', 'version')
    context = {'dps': dps}
    context['num_dps'] = len(dps)
    return render(request, 'crawler/dps.html', context)

def modules(request, id):
    modules = Module.objects.filter(package=id).order_by('name')
    context = {'modules': modules}
    context['num_modules'] = len(modules)
    context['dp'] = Package.objects.get(pk=id)
    return render(request, 'crawler/modules.html', context)
