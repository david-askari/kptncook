from datetime import date
from time import time

import httpx
from pydantic import BaseModel

from .config import settings


class RecipeFromApi(BaseModel):
    date: date
    data: dict

    @property
    def id(self):
        return self.data["_id"]["$oid"]


class KptnCookClient:
    """
    Client for the kptncook api.
    """

    def __init__(
        self, base_url=settings.kptncook_api_url, api_key=settings.kptncook_api_key
    ):
        self.base_url = base_url
        self.headers = {"content-type": "application/json"}
        self.api_key = api_key
        if settings.kptncook_access_token is not None:
            self.headers["Token"] = settings.kptncook_access_token

    @property
    def logged_in(self):
        return "Token" in self.headers

    def to_url(self, path):
        return f"{self.base_url}{path}"

    def __getattr__(self, name):
        """
        Return proxy for httpx, joining base_url with path and
        providing authentication headers automatically.
        """

        def proxy(path, **kwargs):
            url = self.to_url(path)
            set_headers = kwargs.get("headers", {})
            kwargs["headers"] = set_headers | self.headers
            return getattr(httpx, name)(url, **kwargs)

        return proxy

    def list_today(self) -> list[RecipeFromApi]:
        """
        Get all recipes for today from kptncook api.
        """
        time_str = str(time())
        response = self.get(f"/recipes/de/{time_str}?kptnkey={self.api_key}")
        response.raise_for_status()
        recipes = []
        today = date.today()
        for data in response.json():
            recipes.append(RecipeFromApi(date=today, data=data))
        return recipes
