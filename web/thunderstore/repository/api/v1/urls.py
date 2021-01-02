from django.urls import include, path
from rest_framework import routers

from thunderstore.repository.api.v1.views import DeprecateModApiView
from thunderstore.repository.api.v1.viewsets import PackageViewSet
from thunderstore.social.api.v1.views.current_user import CurrentUserInfoView

v1_router = routers.DefaultRouter()
v1_router.register(r"package", PackageViewSet, basename="package")

urls = [
    path("current-user/info/", CurrentUserInfoView.as_view(), name="current-user.info"),
    path("bot/deprecate-mod/", DeprecateModApiView.as_view(), name="bot.deprecate-mod"),
    path("", include(v1_router.urls)),
]
