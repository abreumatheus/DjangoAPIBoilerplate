from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from core.utils import upload_image, delete_image
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    profile_image = serializers.ImageField(write_only=True, required=False)
    profile_image_uuid = serializers.URLField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 'profile_image', 'profile_image_uuid',
            'is_staff')

    def create(self, validated_data):
        if 'profile_image' in validated_data:
            validated_data = upload_image(validated_data, 'profile')

        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        if 'profile_image' in validated_data:
            if instance.profile_image_uuid:
                old_image_id = str(instance.profile_image_uuid)
                delete_image(old_image_id, 'profile')
            validated_data = upload_image(validated_data, 'profile')
            setattr(instance, 'profile_image_uuid', validated_data['profile_image_uuid'])

        if 'password' in validated_data:
            password = validated_data.pop('password')
            hashed_password = make_password(password)
            validated_data['password'] = hashed_password
            setattr(instance, 'password', hashed_password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
