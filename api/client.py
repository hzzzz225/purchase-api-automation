
import logging
import time
import requests

from config.settings import BASE_URL, REQUEST_TIMEOUT


# 创建当前模块的日志记录器
logger = logging.getLogger(__name__)


class ApiClient:

    def __init__(self, token=None):
        self.base_url = BASE_URL.rstrip("/")
        self.token = token
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"

        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")

        if self.token:
            headers.setdefault(
                "Authorization",
                f"Bearer {self.token}"
            )

        # 允许单次请求覆盖默认超时时间
        timeout = kwargs.pop("timeout", REQUEST_TIMEOUT)

        start_time = time.perf_counter()

        logger.info("发送请求：%s %s", method, url)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )

            elapsed = time.perf_counter() - start_time

            logger.info(
                "请求完成：%s %s，状态码：%s，耗时：%.3f秒",
                method,
                url,
                response.status_code,
                elapsed
            )

            return response

        except requests.RequestException:
            elapsed = time.perf_counter() - start_time

            logger.exception(
                "请求异常：%s %s，耗时：%.3f秒",
                method,
                url,
                elapsed
            )

            # 记录异常后继续向上抛出
            raise

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self):
        self.session.close()
