import logging
from dataclasses import dataclass
from time import sleep

from aiohttp import BasicAuth, ClientResponse, ClientSession, ClientTimeout


@dataclass
class AsyncClientConfig:
    retry: int = 99
    timeout: ClientTimeout = ClientTimeout(total=99)
    sleep_time: int = 1
    sleep_time_increment: int = 3


class BaseAsyncClient:
    def __init__(
        self,
        host: str,
        headers: dict | None = None,
        auth: tuple[str, str] | None = None,
    ):
        if not host.endswith("/"):
            host = host + "/"
        basic_auth = BasicAuth(auth[0], auth[1]) if auth else None
        self.__client = ClientSession(
            base_url=host,
            auth=basic_auth,
            headers=headers or {},
        )
        self.__logger = logging.getLogger(self.__class__.__name__)

    async def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        config = config or AsyncClientConfig()
        count, _sleep_time = 0, config.sleep_time
        params, json_data = params or {}, json_data or {}

        while True:
            count += 1
            try:
                self.__logger.debug(
                    f"Request: {method.upper()} {url}\n"
                    f"Params: {params}\n"
                    f"JSON: {json_data}"
                )
                return await self.__client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=config.timeout,
                )
            except Exception as e:
                self.__logger.error(
                    f"Attempt {count}/{config.retry} failed {url}: {str(e)}"
                )
                if count >= config.retry:
                    self.__logger.error(f"Max retries exceeded {url}: {e} ({type(e)})")
                    raise e
                sleep(_sleep_time)
                _sleep_time += config.sleep_time_increment

    async def _get(
        self,
        url: str,
        params: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("GET", url, params, config=config)

    async def _post(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("POST", url, params, json_data, config)

    async def _put(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("PUT", url, params, json_data, config)

    async def _delete(
        self,
        url: str,
        params: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("DELETE", url, params, config=config)

    async def close(self):
        await self.__client.close()
