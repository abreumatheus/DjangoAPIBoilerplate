"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
   https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
   1. Add an import:  from my_app import views
   2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
   1. Add an import:  from other_app.views import Home
   2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
   1. Import the include() function: from django.urls import include, path
   2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from authentication.routes import router as user_router
from authentication.api import TokenObtainPairView, TokenRefreshView


schema_view = get_schema_view(
    openapi.Info(
        title="Basic API",
        default_version='v1',
        description="An API boilerplate.",
        terms_of_service="#",
        contact=openapi.Contact(email="abreumatheus@icloud.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Register your routers here
router = DefaultRouter()
router.registry.extend(user_router.registry)
# ---------------------------


urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'', schema_view.with_ui('redoc', cache_timeout=0), name='Documentation'),
    path(r'api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
