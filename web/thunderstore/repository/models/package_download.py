from datetime import timedelta

from django.db import models
from django.utils import timezone


class PackageVersionDownloadEvent(models.Model):
    version = models.ForeignKey(
        "repository.PackageVersion",
        related_name="download_events",
        on_delete=models.CASCADE,
    )
    source_ip = models.GenericIPAddressField()
    last_download = models.DateTimeField(auto_now_add=True)
    total_downloads = models.PositiveIntegerField(default=1)
    counted_downloads = models.PositiveIntegerField(default=1)

    def count_downloads_and_return_validity(self):
        self.total_downloads += 1
        is_valid = False

        if self.last_download + timedelta(minutes=10) < timezone.now():
            self.counted_downloads += 1
            self.last_download = timezone.now()
            is_valid = True

        self.save(
            update_fields=("total_downloads", "counted_downloads", "last_download")
        )
        return is_valid

    class Meta:
        unique_together = ("version", "source_ip")
