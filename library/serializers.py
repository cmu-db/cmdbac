from models import *
from rest_framework import serializers

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository

class RuntimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runtime

class DatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Database

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package

class DependencySerializer(serializers.ModelSerializer):
    package_info = PackageSerializer(source='package')

    class Meta:
        model = Dependency
        fields = ('id', 'source', 'attempt', 'package_info')

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query

class ActionSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, read_only=True)
    queries = QuerySerializer(many=True, read_only=True)
    class Meta:
        model = Action


class AttemptSerializer(serializers.ModelSerializer):
    repo_info = RepositorySerializer(source='repo')
    runtime_info = RuntimeSerializer(source='runtime')
    database_info = DatabaseSerializer(source='database')
    dependencies = DependencySerializer(source='dependency_set', many=True)
    actions = ActionSerializer(many=True, read_only = True)

    class Meta:
        model = Attempt
        fields = ('id', 'start_time', 'stop_time', 'repo_info', 'sha', 'size', 'log', 'hostname', 
                  'runtime_info', 'database_info', 'result', 'register', 'login', 'actions_count', 'queries_count',
                  'dependencies', 'actions'
            )