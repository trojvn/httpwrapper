import asyncio
import contextlib
import logging
from dataclasses import dataclass
from io import BufferedReader
from time import sleep

from aiohttp import BasicAuth, ClientResponse, ClientSession, ClientTimeout


@dataclass
class AsyncClientConfig:
    retry: int = 99
    timeout: ClientTimeout = ClientTimeout(total=99)
    sleep_time: int = 1
    sleep_time_increment: int = 3
    allow_redirects: bool = False
    proxy: str | None = None


class BaseAsyncClient:
    def __init__(
        self,
        host: str,
        headers: dict | None = None,
        cookies: dict | None = None,
        auth: tuple[str, str] | None = None,
        config: AsyncClientConfig | None = None,
    ):
        if not host.endswith("/"):
            host = host + "/"
        basic_auth = BasicAuth(auth[0], auth[1]) if auth else None
        self.__config = config or AsyncClientConfig()
        self.__connector = None
        self._client = ClientSession(
            base_url=host,
            auth=basic_auth,
            headers=headers or None,
            cookies=cookies or None,
            connector=self.__connector,
            proxy=self.__config.proxy or None,
        )
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.debug(f"Proxy: {self.__config.proxy}")

    async def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        data: BufferedReader | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        if url.startswith("/"):
            url = url[1:]
        config = config or self.__config
        count, _sleep_time = 0, config.sleep_time
        params, json_data = params or None, json_data or None

        while True:
            count += 1
            try:
                message = f"Request: {method.upper()} {url}\nParams: {params}"
                if json_data:
                    message += f"\nJSON: {json_data}"
                if self.__config.proxy:
                    message += f"\nProxy: {self.__config.proxy}"
                self.__logger.debug(message)
                return await self._client.request(
                    url=url,
                    data=data,
                    method=method,
                    params=params,
                    json=json_data,
                    timeout=config.timeout,
                    allow_redirects=config.allow_redirects,
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
        data: BufferedReader | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("POST", url, params, json_data, data, config)

    async def _put(
        self,
        url: str,
        params: dict | None = None,
        json_data: dict | None = None,
        data: BufferedReader | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("PUT", url, params, json_data, data, config)

    async def _delete(
        self,
        url: str,
        params: dict | None = None,
        config: AsyncClientConfig | None = None,
    ) -> ClientResponse:
        return await self._request("DELETE", url, params, config=config)

    async def close(self):
        await self._client.close()

    def __del__(self):
        with contextlib.suppress(Exception):
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())
