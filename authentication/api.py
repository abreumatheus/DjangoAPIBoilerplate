from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenViewBase

from core.permissions import UserCustomPermissionsSet
from core.utils import delete_image
from .models import User
from .serializers import UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserCustomPermissionsSet]
    parser_classes = [MultiPartParser, FormParser]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        if instance.profile_image_uuid:
            image_id = str(instance.profile_image_uuid)
            delete_image(image_id, 'profile')
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenObtainPairView(TokenViewBase):
    serializer_class = serializers.TokenObtainPairSerializer

    @swagger_auto_schema(security=[])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        data = serializer.validated_data

        response = Response(data, status=status.HTTP_200_OK)
        response.set_cookie('auth', data['refresh'], httponly=True)
        return response


class TokenRefreshView(TokenObtainPairView):
    serializer_class = serializers.TokenRefreshSerializer
