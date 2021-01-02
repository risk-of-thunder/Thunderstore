from django.contrib import admin

from thunderstore.repository.models import (
    DiscordUserBotPermission,
    Package,
    PackageRating,
    PackageVersion,
    UploaderIdentity,
    UploaderIdentityMember,
)


@admin.register(PackageRating)
class PackageRatingAdmin(admin.ModelAdmin):
    model = PackageRating
    list_display = (
        "rater",
        "package",
        "date_created",
    )


class UploaderIdentityMemberAdmin(admin.StackedInline):
    model = UploaderIdentityMember
    extra = 0
    list_display = (
        "user",
        "identity",
        "role",
    )


@admin.register(UploaderIdentity)
class UploaderIdentityAdmin(admin.ModelAdmin):
    inlines = [
        UploaderIdentityMemberAdmin,
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        else:
            return []

    readonly_fields = ("name",)
    list_display = ("name",)


class PackageVersionInline(admin.StackedInline):
    model = PackageVersion
    readonly_fields = (
        "date_created",
        "dependencies",
        "description",
        "downloads",
        "file",
        "file_size",
        "icon",
        "name",
        "readme",
        "version_number",
        "website_url",
    )
    extra = 0
    filter_horizontal = ("dependencies",)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    inlines = [
        PackageVersionInline,
    ]

    readonly_fields = (
        "date_created",
        "downloads",
        "name",
        "owner",
        "latest",
    )
    list_display = (
        "name",
        "owner",
        "is_active",
        "is_deprecated",
        "is_pinned",
    )
    list_filter = (
        "is_active",
        "is_pinned",
        "is_deprecated",
    )
    search_fields = (
        "name",
        "owner__name",
    )


@admin.register(DiscordUserBotPermission)
class DiscordUserBotPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "thunderstore_user",
        "label",
        "discord_user_id",
        "can_deprecate",
    )
    list_filter = ("can_deprecate",)
    search_fields = (
        "label",
        "thunderstore_user__username",
    )
