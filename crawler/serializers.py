from models import *
from rest_framework import serializers

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository

class RuntimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runtime

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package

class DependencySerializer(serializers.ModelSerializer):
    package_info = PackageSerializer(source='package')

    class Meta:
        model = Dependency
        fields = ('id', 'source', 'attempt', 'package_info')

class AttemptSerializer(serializers.ModelSerializer):
    repo_info = RepositorySerializer(source='repo')
    runtime_info = RuntimeSerializer(source='runtime')
    dependencies = DependencySerializer(source='dependency_set', many=True)

    class Meta:
        model = Attempt
        fields = ('id', 'start_time', 'stop_time', 'repo_info', 'sha', 'size', 'log', 'hostname', 
                  'runtime_info', 'result', 'register', 'login', 'forms_count', 'queries_count', 
                  'dependencies'
            )