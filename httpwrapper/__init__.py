import logging
from dataclasses import dataclass
from io import BufferedReader
from time import sleep

from httpx import Client, RequestError, Response

from .async_ import AsyncClientConfig, BaseAsyncClient


@dataclass
class ClientConfig:
    retry: int = 99
    timeout: int = 99
    sleep_time: int = 1
    sleep_time_increment: int = 3
    follow_redirects: bool = False


class BaseClient:
    def __init__(
        self,
        host: str,
        headers: dict | None = None,
        cookies: dict | None = None,
        auth: tuple[str, str] | None = None,
        config: ClientConfig | None = None,
    ):
        if host.endswith("/"):
            host = host[:-1]
        self.__config = config or ClientConfig()
        self._client = Client(
            auth=auth,
            base_url=host,
            headers=headers or None,
            cookies=cookies or None,
            follow_redirects=self.__config.follow_redirects,
        )
        self.__logger = logging.getLogger(self.__class__.__name__)

    def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: ClientConfig | None = None,
        content: BufferedReader | None = None,
    ) -> Response:
        config = config or self.__config
        count, _sleep_time = 0, config.sleep_time
        params, json_data = params or None, json_data or None

        while True:
            count += 1
            try:
                self.__logger.debug(
                    f"Request: {method.upper()} {url}\n"
                    f"Params: {params}\n"
                    f"JSON: {json_data}"
                )
                response = self._client.request(
                    url=url,
                    method=method,
                    params=params,
                    json=json_data,
                    content=content,
                    timeout=config.timeout,
                    follow_redirects=config.follow_redirects,
                )
                self.__logger.debug(
                    f"Response: {response.status_code}\n"
                    f"Content: {response.text[:200]}..."
                )
                return response
            except (RequestError, Exception) as e:
                self.__logger.error(
                    f"Attempt {count}/{config.retry} failed {url}: {str(e)}"
                )
                if count >= config.retry:
                    self.__logger.error(f"Max retries exceeded {url}: {e} ({type(e)})")
                    raise e
                sleep(_sleep_time)
                _sleep_time += config.sleep_time_increment

    def _get(
        self,
        url: str,
        params: dict | None = None,
        config: ClientConfig | None = None,
    ) -> Response:
        return self._request("GET", url, params, config=config)

    def _post(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: ClientConfig | None = None,
        content: BufferedReader | None = None,
    ) -> Response:
        return self._request("POST", url, params, json_data, config, content)

    def _put(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: ClientConfig | None = None,
        content: BufferedReader | None = None,
    ) -> Response:
        return self._request("PUT", url, params, json_data, config, content)

    def _delete(
        self,
        url: str,
        params: dict | None = None,
        config: ClientConfig | None = None,
    ) -> Response:
        return self._request("DELETE", url, params, config=config)


__all__ = ["BaseClient", "ClientConfig", "BaseAsyncClient", "AsyncClientConfig"]
