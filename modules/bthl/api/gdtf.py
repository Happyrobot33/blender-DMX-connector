"""GDTF Share API integration module.

Provides functionality to interact with the GDTF Share API:
- Login to GDTF Share account
- Get list of available fixtures
- Download GDTF fixture files
"""

import json
import urllib.request
import urllib.error
import http.cookiejar
import os
from typing import Optional, Dict, List, Any
from pathlib import Path


class GDTFShareAPI:
    """Client for GDTF Share API v1."""

    BASE_URL = "https://gdtf-share.com/apis/public"
    COOKIE_TIMEOUT = 2 * 60 * 60  # 2 hours in seconds

    def __init__(self, cookie_file: Optional[str] = None):
        """Initialize GDTF Share API client.

        Args:
            cookie_file: Path to store session cookies. If None, cookies are stored in temp.
        """
        if cookie_file is None:
            import tempfile
            cookie_file = os.path.join(tempfile.gettempdir(), "gdtf_share_cookies.txt")

        self.cookie_file = cookie_file
        self.cookie_jar = http.cookiejar.MozillaCookieJar(cookie_file)

        # Load existing cookies if they exist
        if os.path.exists(cookie_file):
            try:
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
            except Exception as e:
                print(f"Warning: Could not load cookies: {e}")

        # Set up URL opener with cookie support
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        urllib.request.install_opener(self.opener)

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to GDTF Share API.

        Args:
            endpoint: API endpoint path (e.g., "login.php")
            method: HTTP method (GET or POST)
            data: Dictionary to send as JSON body (for POST requests)

        Returns:
            Response as dictionary

        Raises:
            ConnectionError: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            if method == "POST" and data:
                json_data = json.dumps(data).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={"Content-Type": "application/json"},
                    method=method,
                )
            else:
                req = urllib.request.Request(url, method=method)

            response = urllib.request.urlopen(req)
            response_data = response.read().decode("utf-8")

            # Save cookies after each successful request
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

            return json.loads(response_data)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_json = json.loads(error_body)
                raise ConnectionError(
                    f"HTTP {e.code}: {error_json.get('error', 'Unknown error')}"
                )
            except json.JSONDecodeError:
                raise ConnectionError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to GDTF Share API: {e}")

    def login(self, username: str, password: str) -> bool:
        """Login to GDTF Share.

        Args:
            username: GDTF Share username
            password: GDTF Share password

        Returns:
            True if login successful

        Raises:
            ConnectionError: If login fails
        """
        response = self._request(
            "login.php",
            method="POST",
            data={"user": username, "password": password},
        )

        if response.get("result"):
            print(f"GDTF Login successful: {response.get('notice', '')}")
            return True
        else:
            raise ConnectionError(f"Login failed: {response.get('error', 'Unknown error')}")

    def get_fixture_list(self) -> List[Dict[str, Any]]:
        """Get list of available GDTF fixtures.

        Returns:
            List of fixture dictionaries containing:
            - rid: Revision ID
            - fixture: Fixture name
            - manufacturer: Manufacturer name
            - revision: Revision name
            - rating: Rating (0-5)
            - modes: List of available modes
            - uuid: Unique fixture type ID
            - filesize: File size in bytes
            - and more fields (see GDTF API docs)

        Raises:
            ConnectionError: If request fails
        """
        response = self._request("getList.php")

        if response.get("result"):
            return response.get("list", [])
        else:
            raise ConnectionError(
                f"Failed to get fixture list: {response.get('error', 'Unknown error')}"
            )

    def download_fixture_to_bytes(self, rid: int) -> bytes:
        """Download a GDTF fixture file to memory.

        Args:
            rid: Revision ID of the fixture to download

        Returns:
            File data as bytes

        Raises:
            ConnectionError: If download fails
        """
        url = f"{self.BASE_URL}/downloadFile.php?rid={rid}"

        try:
            response = urllib.request.urlopen(url)
            file_data = response.read()

            # Verify it's a valid GDTF file (should start with <?xml or be a zip)
            if not (
                file_data.startswith(b"<?xml") or file_data.startswith(b"PK")
            ):  # PK is zip magic number
                try:
                    error_json = json.loads(file_data.decode("utf-8"))
                    raise ConnectionError(
                        f"Download failed: {error_json.get('error', 'Unknown error')}"
                    )
                except json.JSONDecodeError:
                    raise ConnectionError("Download failed: Invalid file format")

            return file_data

        except urllib.error.HTTPError as e:
            raise ConnectionError(
                f"HTTP {e.code}: Failed to download fixture (rid={rid})"
            )
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect for download: {e}")

    def download_fixture(self, rid: int, output_path: str) -> bool:
        """Download a GDTF fixture file to disk.

        Args:
            rid: Revision ID of the fixture to download
            output_path: Path where the .gdtf file will be saved

        Returns:
            True if download successful

        Raises:
            ConnectionError: If download fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            file_data = self.download_fixture_to_bytes(rid)

            with open(output_path, "wb") as f:
                f.write(file_data)

            return True

        except Exception as e:
            raise ConnectionError(f"Failed to save fixture file: {str(e)}")

    def search_fixtures(self, query: str, fixtures_list: Optional[List[Dict]] = None) -> List[Dict]:
        """Search fixtures by manufacturer or name.

        Args:
            query: Search query string (case-insensitive)
            fixtures_list: Pre-fetched list of fixtures. If None, will fetch from API.

        Returns:
            List of matching fixtures
        """
        if fixtures_list is None:
            fixtures_list = self.get_fixture_list()

        query_lower = query.lower()
        results = []

        for fixture in fixtures_list:
            if (
                query_lower in fixture.get("fixture", "").lower()
                or query_lower in fixture.get("manufacturer", "").lower()
            ):
                results.append(fixture)

        return results

    def is_logged_in(self) -> bool:
        """Check if currently logged in by verifying cookies exist.

        Returns:
            True if session cookie exists, False otherwise
        """
        try:
            for cookie in self.cookie_jar:
                if cookie.name.lower() == "phpsessid":
                    return True
        except Exception:
            pass
        return False
