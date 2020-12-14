from rest_framework.routers import SimpleRouter

from .api import UserViewSet

app_name = "user"
router = SimpleRouter()

router.register(r"user", UserViewSet, basename="user")

urlpatterns = router.urls
