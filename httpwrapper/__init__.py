import logging
from dataclasses import dataclass
from time import sleep

from httpx import Client, RequestError, Response


@dataclass
class RequestConfig:
    retry = 99
    timeout = 99
    sleep_time = 1
    sleep_time_increment = 3


class BaseClient:
    def __init__(
        self,
        host: str,
        headers: dict | None = None,
        auth: tuple[str, str] | None = None,
    ):
        if host.endswith("/"):
            host = host[:-1]
        self.__client = Client(base_url=host, headers=headers or {}, auth=auth)
        self.__logger = logging.getLogger(self.__class__.__name__)

    def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        request_config: RequestConfig | None = None,
    ) -> Response:
        request_config = request_config or RequestConfig()
        count, _sleep_time = 0, request_config.sleep_time
        params, json_data = params or {}, json_data or {}

        while True:
            count += 1
            try:
                self.__logger.debug(
                    f"Request: {method.upper()} {url}\n"
                    f"Params: {params}\n"
                    f"JSON: {json_data}"
                )
                response = self.__client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=request_config.timeout,
                )
                self.__logger.debug(
                    f"Response: {response.status_code}\n"
                    f"Content: {response.text[:200]}..."
                )
                return response
            except (RequestError, Exception) as e:
                self.__logger.error(
                    f"Attempt {count}/{request_config.retry} failed {url}: {str(e)}"
                )
                if count >= request_config.retry:
                    self.__logger.error(f"Max retries exceeded {url}: {e} ({type(e)})")
                    raise e
                sleep(_sleep_time)
                _sleep_time += request_config.sleep_time_increment

    def _get(
        self,
        url: str,
        params: dict | None = None,
        config: RequestConfig | None = None,
    ) -> Response:
        return self._request("GET", url, params=params, request_config=config)

    def _post(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: RequestConfig | None = None,
    ) -> Response:
        return self._request(
            "POST", url, params=params, json_data=json_data, request_config=config
        )

    def _put(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: RequestConfig | None = None,
    ) -> Response:
        return self._request(
            "PUT", url, params=params, json_data=json_data, request_config=config
        )

    def _delete(
        self,
        url: str,
        params: dict | None = None,
        config: RequestConfig | None = None,
    ) -> Response:
        return self._request("DELETE", url, params=params, request_config=config)
