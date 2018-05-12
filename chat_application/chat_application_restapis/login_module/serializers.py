from django.contrib.auth.models import User, Group
from rest_framework_mongoengine import serializers
from models import User as UserModel


class UserSerializer(serializers.DocumentSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'