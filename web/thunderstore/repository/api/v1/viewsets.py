import json

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from thunderstore.core.cache import BackgroundUpdatedCacheMixin
from thunderstore.core.utils import CommunitySiteSerializerContext
from thunderstore.repository.api.v1.serializers import PackageListingSerializer
from thunderstore.repository.cache import get_package_listing_queryset
from thunderstore.repository.models import PackageRating


class PackageViewSet(
    BackgroundUpdatedCacheMixin,
    CommunitySiteSerializerContext,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = PackageListingSerializer
    lookup_field = "package__uuid4"
    lookup_url_kwarg = "uuid4"

    @classmethod
    def get_no_cache_response(cls):
        return HttpResponse(
            json.dumps({"error": "No cache available"}),
            status=503,
            content_type="application/json",
        )

    def get_object(self):
        return super().get_object()

    def get_queryset(self):
        return get_package_listing_queryset(community_site=self.request.community_site)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def rate(self, request, uuid4=None):
        package = self.get_object().package
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Must be logged in")
        target_state = request.data.get("target_state")
        if target_state == "rated":
            PackageRating.objects.get_or_create(rater=user, package=package)
            result_state = "rated"
        else:
            PackageRating.objects.filter(rater=user, package=package).delete()
            result_state = "unrated"
        return Response(
            {
                "state": result_state,
                "score": package.rating_score,
            }
        )
