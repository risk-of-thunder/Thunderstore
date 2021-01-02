import base64
import hashlib
import json

import requests


class AuthorizedSession:
    def __init__(
        self,
        account_id,
        api_url,
        download_url,
        authorization_token,
        absolute_minimum_part_size,
        recommended_part_size,
        allowed,
    ):
        self.account_id = account_id
        self.api_url = api_url
        self.download_url = download_url
        self.authorization_token = authorization_token
        self.absolute_minimum_part_size = absolute_minimum_part_size
        self.recommended_part_size = recommended_part_size
        self.allowed = allowed

    @property
    def bucket_name(self):
        return self.allowed["bucketName"]

    def get_api_url(self, endpoint):
        return f"{self.api_url}{endpoint}"

    def get_download_url_by_id(self, file_id):
        endpoint = f"/b2api/v2/b2_download_file_by_id?fileId={file_id}"
        return f"{self.download_url}{endpoint}"

    def get_download_url_by_name(self, file_name):
        return f"{self.download_url}/file/{self.bucket_name}/{file_name}"

    @classmethod
    def from_response(cls, response):
        data = response.json()
        return cls(
            account_id=data["accountId"],
            api_url=data["apiUrl"],
            download_url=data["downloadUrl"],
            authorization_token=data["authorizationToken"],
            absolute_minimum_part_size=data["absoluteMinimumPartSize"],
            recommended_part_size=data["recommendedPartSize"],
            allowed=data["allowed"],
        )

    @classmethod
    def authorize_account(cls, application_key_id, application_key):
        authorization_token = base64.b64encode(
            f"{application_key_id}:{application_key}".encode("utf-8")
        ).decode("utf-8")
        headers = {
            "Authorization": f"Basic: {authorization_token}",
        }
        response = requests.get(
            "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
            headers=headers,
        )
        # TODO: Handle 400 bad_request (invalid request data)
        # TODO: Handle 401 unauthorized (key ID or key is wrong)
        # TODO: Handle 401 unsupported (key valid but cannot be used)
        response.raise_for_status()
        return cls.from_response(response)


class UploadSession:
    def __init__(self, bucket_id, upload_url, authorization_token):
        self.bucket_id = bucket_id
        self.upload_url = upload_url
        self.authorization_token = authorization_token

    @classmethod
    def from_response(cls, response):
        data = response.json()
        return cls(
            bucket_id=data["authorizationToken"],
            upload_url=data["uploadUrl"],
            authorization_token=data["authorizationToken"],
        )


class BackblazeB2API:
    def __init__(self, application_key_id, application_key, bucket_id):
        self.application_key_id = application_key_id
        self.application_key = application_key
        self.bucket_id = bucket_id
        # TODO: Support bucket name by checking it from the authorized session's
        #       "allowed" field
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self.refresh_session()
        return self._session

    def refresh_session(self):
        self._session = AuthorizedSession.authorize_account(
            application_key_id=self.application_key_id,
            application_key=self.application_key,
        )
        if self._session.allowed["bucketId"] != self.bucket_id:
            raise RuntimeError("Invalid bucket ID received")

    def _authorize_request_params(self, request_params):
        headers = request_params.get("headers", {})
        headers.update(
            {
                "Authorization": self.session.authorization_token,
            }
        )
        request_params["headers"] = headers
        return request_params

    def do_request(self, request_func, url, **params):
        # TODO: Add generic Backblaze error status code handling
        # 503: Generic timeout or service failure, should retry
        # 401: Invalid or expired auth token, should retry
        retry_statuscodes = (503, 401)
        attempts_left = 3
        while attempts_left > 0:
            request_params = self._authorize_request_params(params)
            response = request_func(url, **request_params)
            if response.status_code == 401:
                self.refresh_session()
            if response.status_code not in retry_statuscodes:
                break
            attempts_left -= 1
        response.raise_for_status()
        return response

    def do_get_request(self, url, **kwargs):
        return self.do_request(requests.get, url, **kwargs)

    def do_post_request(self, url, **kwargs):
        return self.do_request(requests.post, url, **kwargs)

    def create_upload_session(self):
        url = self.session.get_api_url("/b2api/v2/b2_get_upload_url")
        params = {
            "bucketId": self.bucket_id,
        }
        response = self.do_get_request(url, params=params)
        # TODO: Handle 400 bad_request (invalid request data)
        # TODO: Handle 401 unauthorized (valid auth token but no privileges)
        # TODO: Handle 401 bad_auth_token (invalid auth token)
        # TODO: Handle 401 expired_auth_token (expired auth token)
        # TODO: Handle 503 service_unavailable
        response.raise_for_status()
        return UploadSession.from_response(response)

    def list_file_names(self, start_file_name="", prefix=""):
        request_content = {
            "bucketId": self.bucket_id,
        }
        if start_file_name:
            request_content["startFileName"] = start_file_name
        if prefix:
            request_content["prefix"] = prefix

        response = self.do_post_request(
            f"{self.session.api_url}/b2api/v2/b2_list_file_names",
            data=json.dumps(request_content),
        )
        # TODO: Handle 400 bad_request (invalid request data)
        # TODO: Handle 400 invalid_bucket_id (invalid bucket ID)
        # TODO: Handle 400 out_of_range (maxFileCount out of bounds)
        # TODO: Handle 401 unauthorized (valid auth token but no privileges)
        # TODO: Handle 401 bad_auth_token (invalid auth token)
        # TODO: Handle 401 expired_auth_token (expired auth token)
        # TODO: Handle 503 bad_request (timeout iterating and filtering files)
        response.raise_for_status()
        return response.json()

    def upload_file(self, name, content):
        content.seek(0)
        content_sha1 = hashlib.sha1(content.read()).hexdigest()
        content_size = content.size

        def attempt_upload(auth_token):
            headers = {
                "Authorization": auth_token,
                "Content-Type": "b2/x-auto",
                "Content-Length": str(content_size),
                "X-Bz-File-Name": name,
                "X-Bz-Content-Sha1": content_sha1,
                # TODO: Add last modified header
            }

            content.seek(0)
            return requests.post(
                upload_session.upload_url,
                headers=headers,
                data=content,
            )

        # TODO: Handle 400 bad_request (invalid request data)
        # TODO: Handle 401 unauthorized (valid auth token but no privileges)
        # TODO: Handle 401 bad_auth_token (invalid auth token)
        # TODO: Handle 401 expired_auth_token (expired auth token)
        # TODO: Handle 403 cap_exceeded (usage cap exceeded)
        # TODO: Handle 405 method_not_allowed (only post is supported)
        # TODO: Handle 408 request_timeout (service timeouted during upload)
        # TODO: Handle 503 service_unavailable (retry upload with a new session)
        upload_session = self.create_upload_session()
        attempts_left = 3
        while attempts_left > 0:
            response = attempt_upload(upload_session.authorization_token)
            if response.status_code == 503:
                upload_session = self.create_upload_session()
            if response.status_code == 401:
                self.refresh_session()
            if response.status_code not in (503, 408, 401):
                break
            attempts_left -= 1
        response.raise_for_status()
        return response  # TODO: Return a python object of the data

    def get_file_url(self, file_name):
        return self.session.get_download_url_by_name(file_name)

    def download_file(self, file_id):
        url = self.session.get_download_url(file_id)
        response = self.do_get_request(url)  # TODO: Use streaming
        # TODO: Handle 400 bad_request (invalid request data)
        # TODO: Handle 401 unauthorized (valid auth token but no privileges)
        # TODO: Handle 401 bad_auth_token (invalid auth token)
        # TODO: Handle 401 expired_auth_token (expired auth token)
        # TODO: Handle 404 not_found (file not found in b2)
        # TODO: Handle 416 range_not_satisfiable (invalid requested data range)
        response.raise_for_status()
        return response.content
