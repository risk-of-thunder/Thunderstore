from thunderstore.community.models import CommunitySite, PackageListing, Q
from thunderstore.core.cache import CacheBustCondition, cache_function_result


@cache_function_result(cache_until=CacheBustCondition.any_package_updated)
def get_package_listing_queryset(community_site: CommunitySite):
    return (
        PackageListing.objects.active()
        .exclude(~Q(community=community_site.community))
        .select_related(
            "package",
            "package__owner",
            "package__latest",
        )
        .prefetch_related(
            "package__versions",
            "package__versions__dependencies",
        )
        .order_by(
            "-package__is_pinned", "package__is_deprecated", "-package__date_updated"
        )
    )
