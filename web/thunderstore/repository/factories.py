import factory
from factory.django import DjangoModelFactory

from thunderstore.core.factories import UserFactory

from .models import (
    Package,
    PackageVersion,
    PackageVersionDownloadEvent,
    UploaderIdentity,
    UploaderIdentityMember,
)


class UploaderIdentityFactory(DjangoModelFactory):
    class Meta:
        model = UploaderIdentity

    name = factory.Faker("first_name")


class UploaderIdentityMemberFactory(DjangoModelFactory):
    class Meta:
        model = UploaderIdentityMember

    user = factory.SubFactory(UserFactory)
    identity = factory.SubFactory(UploaderIdentityFactory)


class PackageFactory(DjangoModelFactory):
    class Meta:
        model = Package

    owner = factory.SubFactory(UploaderIdentityFactory)
    name = factory.Faker("first_name")


class PackageVersionFactory(DjangoModelFactory):
    class Meta:
        model = PackageVersion

    package = factory.lazy_attribute(lambda o: PackageFactory.create(name=o.name))
    icon = factory.django.ImageField(width=256, height=256)
    name = factory.Faker("first_name")
    version_number = "1.0.0"
    file_size = 5242880


class PackageVersionDownloadEventFactory(DjangoModelFactory):
    class Meta:
        model = PackageVersionDownloadEvent

    version = factory.SubFactory(PackageVersionFactory)
