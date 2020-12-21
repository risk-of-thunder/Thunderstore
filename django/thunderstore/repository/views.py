from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from thunderstore.community.models import PackageCategory, PackageListing
from thunderstore.repository.models import PackageVersion, UploaderIdentity
from thunderstore.repository.package_upload import PackageUploadForm

# Should be divisible by 4 and 3
MODS_PER_PAGE = 24


class PackageListSearchView(ListView):
    model = PackageListing
    paginate_by = MODS_PER_PAGE

    def get_base_queryset(self):
        return self.model.objects.active().exclude(~Q(community=self.request.community))

    def get_page_title(self):
        return ""

    def get_cache_vary(self):
        return ""

    def get_categories(self):
        return PackageCategory.objects.exclude(~Q(community=self.request.community))

    def get_full_cache_vary(self):
        cache_vary = self.get_cache_vary()
        cache_vary += f".{self.request.community.identifier}"
        cache_vary += f".{self.get_search_query()}"
        cache_vary += f".{self.get_active_ordering()}"
        cache_vary += f".{self.get_selected_categories()}"
        cache_vary += f".{self.get_is_deprecated_included()}"
        cache_vary += f".{self.get_is_nsfw_included()}"
        return cache_vary

    def get_ordering_choices(self):
        return (
            ("last-updated", "Last updated"),
            ("newest", "Newest"),
            ("most-downloaded", "Most downloaded"),
            ("top-rated", "Top rated"),
        )

    def get_selected_categories(self):
        selections = self.request.GET.getlist("categories", [])
        result = []
        for selection in selections:
            try:
                result.append(int(selection))
            except ValueError:
                pass
        return result

    def get_is_nsfw_included(self):
        try:
            return bool(self.request.GET.get("nsfw", False))
        except ValueError:
            return False

    def get_is_deprecated_included(self):
        try:
            return bool(self.request.GET.get("deprecated", False))
        except ValueError:
            return False

    def get_active_ordering(self):
        ordering = self.request.GET.get("ordering", "last-updated")
        possibilities = [x[0] for x in self.get_ordering_choices()]
        if ordering not in possibilities:
            return possibilities[0]
        return ordering

    def get_search_query(self):
        return self.request.GET.get("q", "")

    def order_queryset(self, queryset):
        active_ordering = self.get_active_ordering()
        if active_ordering == "newest":
            return queryset.order_by(
                "-package__is_pinned",
                "package__is_deprecated",
                "-package__date_created",
            )
        if active_ordering == "most-downloaded":
            return queryset.annotate(
                total_downloads=Sum("package__versions__downloads")
            ).order_by(
                "-package__is_pinned",
                "package__is_deprecated",
                "-total_downloads",
            )
        if active_ordering == "top-rated":
            return queryset.annotate(
                total_rating=Count("package__package_ratings")
            ).order_by(
                "-package__is_pinned",
                "package__is_deprecated",
                "-total_rating",
            )
        return queryset.order_by(
            "-package__is_pinned",
            "package__is_deprecated",
            "-package__date_updated",
        )

    def perform_search(self, queryset, search_query):
        search_fields = (
            "package__name",
            "package__owner__name",
            "package__latest__description",
        )

        icontains_query = Q()
        parts = search_query.split(" ")
        for part in parts:
            for field in search_fields:
                icontains_query &= ~Q(**{f"{field}__icontains": part})

        return queryset.exclude(icontains_query).distinct()

    def get_queryset(self):
        queryset = (
            self.get_base_queryset()
            .prefetch_related("package__versions")
            .select_related(
                "package",
                "package__latest",
                "package__owner",
            )
        )
        selected_categories = self.get_selected_categories()
        if selected_categories:
            category_queryset = Q()
            for category in selected_categories:
                category_queryset &= Q(categories=category)
            queryset = queryset.exclude(~category_queryset)
        if not self.get_is_nsfw_included():
            queryset = queryset.exclude(has_nsfw_content=True)
        if not self.get_is_deprecated_included():
            queryset = queryset.exclude(package__is_deprecated=True)
        search_query = self.get_search_query()
        if search_query:
            queryset = self.perform_search(queryset, search_query)
        return self.order_queryset(queryset)

    def get_breadcrumbs(self):
        return [
            {
                "url": reverse_lazy("packages.list"),
                "name": "Packages",
            }
        ]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["categories"] = self.get_categories()
        context["selected_categories"] = self.get_selected_categories()
        context["nsfw_included"] = self.get_is_nsfw_included()
        context["deprecated_included"] = self.get_is_deprecated_included()
        context["cache_vary"] = self.get_full_cache_vary()
        context["page_title"] = self.get_page_title()
        context["ordering_modes"] = self.get_ordering_choices()
        context["active_ordering"] = self.get_active_ordering()
        context["current_search"] = self.get_search_query()
        breadcrumbs = self.get_breadcrumbs()
        if len(breadcrumbs) > 1:
            context["breadcrumbs"] = breadcrumbs
        return context


class PackageListView(PackageListSearchView):
    def get_page_title(self):
        return f"All mods"

    def get_cache_vary(self):
        return "all"


class PackageListByOwnerView(PackageListSearchView):
    def get_breadcrumbs(self):
        breadcrumbs = super().get_breadcrumbs()
        return breadcrumbs + [
            {
                "url": reverse_lazy("packages.list_by_owner", kwargs=self.kwargs),
                "name": self.owner.name,
            }
        ]

    def cache_owner(self):
        self.owner = get_object_or_404(UploaderIdentity, name=self.kwargs["owner"])

    def dispatch(self, *args, **kwargs):
        self.cache_owner()
        return super().dispatch(*args, **kwargs)

    def get_base_queryset(self):
        return self.model.objects.active().exclude(
            ~Q(Q(package__owner=self.owner) & Q(community=self.request.community))
        )

    def get_page_title(self):
        return f"Mods uploaded by {self.owner.name}"

    def get_cache_vary(self):
        return f"authorer-{self.owner.name}"


class PackageListByDependencyView(PackageListSearchView):
    package_listing: PackageListing

    def cache_package_listing(self):
        owner = self.kwargs["owner"]
        owner = get_object_or_404(UploaderIdentity, name=owner)
        name = self.kwargs["name"]
        package_listing = (
            self.model.objects.active()
            .filter(
                package__owner=owner,
                package__name=name,
                community=self.request.community,
            )
            .first()
        )
        if not package_listing:
            raise Http404("No matching package found")
        self.package_listing = package_listing

    def dispatch(self, *args, **kwargs):
        self.cache_package_listing()
        return super().dispatch(*args, **kwargs)

    def get_base_queryset(self):
        return PackageListing.objects.exclude(
            ~Q(package__in=self.package_listing.package.dependants)
        )

    def get_page_title(self):
        return f"Mods that depend on {self.package_listing.package.display_name}"

    def get_cache_vary(self):
        return f"dependencies-{self.package_listing.package.id}"


class PackageDetailView(DetailView):
    model = PackageListing

    def get_object(self, *args, **kwargs):
        owner = self.kwargs["owner"]
        owner = get_object_or_404(UploaderIdentity, name=owner)
        name = self.kwargs["name"]
        package_listing = (
            self.model.objects.active()
            .filter(
                package__owner=owner,
                package__name=name,
                community=self.request.community,
            )
            .first()
        )
        if not package_listing:
            raise Http404("No matching package found")
        return package_listing

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        package_listing = context["object"]
        dependant_count = package_listing.package.dependants.active().count()

        if dependant_count == 1:
            dependants_string = f"{dependant_count} other mod depends on this mod"
        else:
            dependants_string = f"{dependant_count} other mods depend on this mod"

        context["dependants_string"] = dependants_string
        return context


class PackageVersionDetailView(DetailView):
    model = PackageVersion

    def get_object(self, *args, **kwargs):
        owner = self.kwargs["owner"]
        name = self.kwargs["name"]
        version = self.kwargs["version"]
        listing = get_object_or_404(
            PackageListing,
            package__owner__name=owner,
            package__name=name,
            community=self.request.community,
        )
        version = get_object_or_404(
            PackageVersion, package=listing.package, version_number=version
        )
        return version


class PackageCreateView(CreateView):
    model = PackageVersion
    form_class = PackageUploadForm
    template_name = "repository/package_create.html"

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("index")
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["user"] = self.request.user
        kwargs["community"] = self.request.community
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        instance = form.save()
        return redirect(instance)


class PackageDownloadView(View):
    def get(self, *args, **kwargs):
        owner = kwargs["owner"]
        name = kwargs["name"]
        version = kwargs["version"]

        listing = get_object_or_404(
            PackageListing,
            package__owner__name=owner,
            package__name=name,
            community=self.request.community,
        )
        version = get_object_or_404(
            PackageVersion, package=listing.package, version_number=version
        )
        version.maybe_increase_download_counter(self.request)
        return redirect(self.request.build_absolute_uri(version.file.url))
