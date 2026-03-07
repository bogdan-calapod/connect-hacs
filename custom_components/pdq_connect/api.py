"""PDQ Connect API client."""
from __future__ import annotations

import logging
from typing import Any

import requests

from .const import (
    API_DEPLOYMENTS,
    API_DEVICE,
    API_DEVICES,
    API_GROUPS,
    API_PACKAGE,
    API_PACKAGES,
)

_LOGGER = logging.getLogger(__name__)

# Maximum page size accepted by the API
_PAGE_SIZE = 100


class PDQConnectAuthError(Exception):
    """Raised when authentication fails (401)."""


class PDQConnectAPIError(Exception):
    """Raised on non-auth API errors."""


class PDQConnectAPI:
    """Thin wrapper around the PDQ Connect REST API."""

    def __init__(self, api_key: str) -> None:
        """Initialise the client with a Bearer token."""
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """
        Validate credentials by fetching the first page of devices.

        Raises PDQConnectAuthError on 401.
        Returns True on success.
        """
        self.list_devices(page=1, page_size=1)
        return True

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------

    def list_devices(
        self,
        *,
        page: int = 1,
        page_size: int = _PAGE_SIZE,
        includes: str | None = None,
        group: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a page of devices."""
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if includes:
            params["includes"] = includes
        if group:
            params["group"] = group
        return self._get(API_DEVICES, params=params).get("data", [])

    def list_all_devices(self, includes: str | None = None) -> list[dict[str, Any]]:
        """Fetch every device, handling pagination automatically."""
        devices: list[dict[str, Any]] = []
        page = 1
        while True:
            page_data = self.list_devices(page=page, page_size=_PAGE_SIZE, includes=includes)
            devices.extend(page_data)
            if len(page_data) < _PAGE_SIZE:
                break
            page += 1
        return devices

    def get_device(self, device_id: str) -> dict[str, Any]:
        """Return a single device by ID."""
        url = API_DEVICE.format(device_id=device_id)
        return self._get(url).get("data", {})

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------

    def list_all_groups(self) -> list[dict[str, Any]]:
        """Fetch every group, handling pagination."""
        groups: list[dict[str, Any]] = []
        page = 1
        while True:
            page_data = self._get(
                API_GROUPS, params={"page": page, "pageSize": _PAGE_SIZE}
            ).get("data", [])
            groups.extend(page_data)
            if len(page_data) < _PAGE_SIZE:
                break
            page += 1
        return groups

    # ------------------------------------------------------------------
    # Packages
    # ------------------------------------------------------------------

    def list_all_packages(self) -> list[dict[str, Any]]:
        """Fetch every package, handling pagination."""
        packages: list[dict[str, Any]] = []
        page = 1
        while True:
            page_data = self._get(
                API_PACKAGES, params={"page": page, "pageSize": _PAGE_SIZE}
            ).get("data", [])
            packages.extend(page_data)
            if len(page_data) < _PAGE_SIZE:
                break
            page += 1
        return packages

    def get_package(self, package_id: str) -> dict[str, Any]:
        """Return a single package (with versions) by ID."""
        url = API_PACKAGE.format(package_id=package_id)
        return self._get(url).get("data", {})

    # ------------------------------------------------------------------
    # Deployments
    # ------------------------------------------------------------------

    def deploy_package(self, package_id: str, target_ids: list[str]) -> None:
        """
        Trigger a package deployment.

        Args:
            package_id: Package ID or Package Version ID (e.g. pkg_... or pkgver_...)
            target_ids: List of Device IDs and/or Group IDs to deploy to.
        """
        params = {
            "package": package_id,
            "targets": ",".join(target_ids),
        }
        self._post(API_DEPLOYMENTS, params=params)
        _LOGGER.info(
            "Deployment triggered: package=%s targets=%s", package_id, target_ids
        )

    # ------------------------------------------------------------------
    # Internal request helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        _LOGGER.debug("GET %s params=%s", url, params)
        response = self._session.get(url, params=params, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def _post(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        _LOGGER.debug("POST %s params=%s", url, params)
        response = self._session.post(url, params=params, json=json, timeout=15)
        self._raise_for_status(response)
        # Deployments returns 204 No Content on success
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.status_code == 401:
            raise PDQConnectAuthError(
                "PDQ Connect returned 401 – check your API key."
            )
        if response.status_code >= 400:
            raise PDQConnectAPIError(
                f"PDQ Connect API error {response.status_code}: {response.text}"
            )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()
