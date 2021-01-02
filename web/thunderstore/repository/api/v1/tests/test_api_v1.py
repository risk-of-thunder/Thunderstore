import json

import pytest

from thunderstore.core.factories import UserFactory
from thunderstore.repository.api.v1.tasks import update_api_v1_caches


@pytest.mark.django_db
def test_api_v1(client, active_package_listing, community_site):
    update_api_v1_caches()
    response = client.get("/api/v1/package/", HTTP_HOST=community_site.site.domain)
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["name"] == active_package_listing.package.name
    assert result[0]["full_name"] == active_package_listing.package.full_package_name

    uuid = result[0]["uuid4"]
    response = client.get(
        f"/api/v1/package/{uuid}/", HTTP_HOST=community_site.site.domain
    )
    assert response.status_code == 200
    assert response.json() == result[0]


@pytest.mark.django_db
def test_api_v1_rate_package(client, active_package_listing, community_site):
    uuid = active_package_listing.package.uuid4
    user = UserFactory.create()
    client.force_login(user)
    response = client.post(
        f"/api/v1/package/{uuid}/rate/",
        json.dumps({"target_state": "rated"}),
        content_type="application/json",
        HTTP_HOST=community_site.site.domain,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "rated"
    assert result["score"] == 1

    response = client.post(
        f"/api/v1/package/{uuid}/rate/",
        json.dumps({"target_state": "unrated"}),
        content_type="application/json",
        HTTP_HOST=community_site.site.domain,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["state"] == "unrated"
    assert result["score"] == 0
