from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property

from thunderstore.core.mixins import TimestampMixin


class PackageListingQueryset(models.QuerySet):
    def active(self):
        return self.exclude(package__is_active=False).exclude(
            ~Q(package__versions__is_active=True),
        )


# TODO: Add a db constraint that ensures a package listing and it's categories
#       belong to the same community. This might require actually specifying
#       the intermediate model in code rather than letting Django handle it
class PackageListing(TimestampMixin, models.Model):
    """
    Represents a package's relation to how it's displayed on the site and APIs
    """

    objects = PackageListingQueryset.as_manager()

    community = models.ForeignKey(
        "community.Community",
        related_name="package_listings",
        on_delete=models.CASCADE,
    )
    package = models.ForeignKey(
        "repository.Package",
        related_name="package_listings",
        on_delete=models.CASCADE,
    )
    categories = models.ManyToManyField(
        "community.PackageCategory",
        related_name="packages",
        blank=True,
    )
    has_nsfw_content = models.BooleanField(default=False)

    def __str__(self):
        return self.package.name

    def get_absolute_url(self):
        return reverse(
            "packages.detail",
            kwargs={"owner": self.package.owner.name, "name": self.package.name},
        )

    @cached_property
    def owner_url(self):
        return reverse(
            "packages.list_by_owner",
            kwargs={"owner": self.package.owner.name},
        )

    @cached_property
    def dependants_url(self):
        return reverse(
            "packages.list_by_dependency",
            kwargs={
                "owner": self.package.owner.name,
                "name": self.package.name,
            },
        )
