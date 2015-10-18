from models import *
from rest_framework import serializers


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt