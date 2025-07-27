from rest_framework import serializers
from .models import getuserdata

class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = getuserdata
        fields = '__all__'
