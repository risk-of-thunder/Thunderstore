from datetime import datetime
from typing import List, Optional, TypedDict

import ulid2
from django.conf import settings
from django.core.exceptions import PermissionDenied
from mypy_boto3_s3 import Client
from mypy_boto3_s3.type_defs import CompletedPartTypeDef

from thunderstore.core.types import UserType
from thunderstore.usermedia.exceptions import (
    S3BucketNameMissingException,
    S3FileKeyChangedException,
)
from thunderstore.usermedia.models import UserMedia
from thunderstore.usermedia.models.usermedia import UserMediaStatus


def create_upload(
    client: Client, user: UserType, filename: str, expiry: Optional[datetime] = None
) -> UserMedia:
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    if not bucket_name:
        raise S3BucketNameMissingException()

    user_media = UserMedia(
        uuid=ulid2.generate_ulid_as_uuid(),
        filename=filename,
        status=UserMediaStatus.initial,
        owner=user,
        prefix=settings.AWS_LOCATION,
        expiry=expiry,
    )
    user_media.key = user_media.compute_key()
    user_media.save()

    response = client.create_multipart_upload(
        Bucket=bucket_name,
        Key=user_media.key,
        Metadata=user_media.s3_metadata,
    )
    user_media.upload_id = response["UploadId"]
    user_media.status = UserMediaStatus.upload_created
    user_media.save(update_fields=("upload_id", "status"))
    return user_media


UploadPartUrlTypeDef = TypedDict(
    "UploadPartUrlTypeDef", {"part_number": int, "url": str}, total=False
)


def get_signed_upload_urls(
    user: UserType, client: Client, user_media: UserMedia, part_count: int
) -> List[UploadPartUrlTypeDef]:
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    if not bucket_name:
        raise S3BucketNameMissingException()

    if not user_media.can_user_write(user):
        raise PermissionDenied()

    upload_urls = []
    for part_number in range(1, part_count + 1):
        upload_urls.append(
            {
                "part_number": part_number,
                "url": client.generate_presigned_url(
                    ClientMethod="upload_part",
                    Params={
                        "Bucket": bucket_name,
                        "Key": user_media.key,
                        "UploadId": user_media.upload_id,
                        "PartNumber": part_number,
                    },
                    ExpiresIn=60 * 60 * 6,
                ),
            }
        )

    return upload_urls


def finalize_upload(
    user: UserType,
    client: Client,
    user_media: UserMedia,
    parts: List[CompletedPartTypeDef],
):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    if not bucket_name:
        raise S3BucketNameMissingException()

    if not user_media.can_user_write(user):
        raise PermissionDenied()

    parts = sorted(parts, key=lambda x: x["PartNumber"])

    result = client.complete_multipart_upload(
        Bucket=bucket_name,
        Key=user_media.key,
        MultipartUpload={
            "Parts": parts,
        },
        UploadId=user_media.upload_id,
    )

    if result["Key"] != user_media.key:
        user_media.status = UserMediaStatus.upload_error
        user_media.save(update_fields=("status",))
        raise S3FileKeyChangedException(user_media.key, result["Key"])
    else:
        meta = client.head_object(
            Bucket=bucket_name,
            Key=user_media.key,
        )
        user_media.size = meta["ContentLength"]
        user_media.status = UserMediaStatus.upload_complete
        user_media.save(update_fields=("status", "size"))


# TODO: Implement
# We should implement abort_upload to abort uploads by user action, or just
# to clean up organically interrupted uploads. If uploads aren't aborted,
# they will remain on the storage backend indefinitely. See
# https://docs.aws.amazon.com/AmazonS3/latest/API/API_AbortMultipartUpload.html
def abort_upload():
    pass


# TODO: Implement
# Might be needed to properly clean up interrupted or aborted uploads
def list_upload_parts():
    pass
