"""
Aether Forge - Secure HTTP Client
Wraps httpx to prevent Server-Side Request Forgery (SSRF) attacks.
Mitigates TOCTOU DNS rebinding by pinning the connection to the validated IP.
"""

import asyncio
import logging
import ipaddress
import socket
import urllib.parse
from typing import Optional, Any, List, Union
import httpx

logger = logging.getLogger("AetherSecureHTTP")

def _validate_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Block private, loopback, link-local, multicast, and unspecified (0.0.0.0)
        if (ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_unspecified):
            return False
        return True
    except ValueError:
        return False

def _is_safe_hostname(hostname: str) -> Optional[bool]:
    # Check if hostname is an IP literal
    try:
        ip = ipaddress.ip_address(hostname)
        if (ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_unspecified):
            logger.warning(f"SSRF Protection: Blocked access to IP literal: {hostname}")
            return False
        return True
    except ValueError:
        return None

async def resolve_and_validate_async(hostname: str) -> Optional[str]:
    # Check if it's already an IP
    is_safe_literal = _is_safe_hostname(hostname)
    if is_safe_literal is False:
        return None
    if is_safe_literal is True:
        return hostname

    # It's a domain, resolve it
    try:
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(hostname, None)
        # Check all IPs, pick the first safe one
        for info in infos:
            ip_str = info[4][0]
            if _validate_ip(ip_str):
                return ip_str
            else:
                logger.warning(f"SSRF Protection: Blocked access to resolved private IP: {hostname} -> {ip_str}")
        return None # All resolved IPs are unsafe
    except socket.gaierror:
        logger.warning(f"SSRF Protection: DNS resolution failed for {hostname}")
        return None
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return None

def resolve_and_validate_sync(hostname: str) -> Optional[str]:
    is_safe_literal = _is_safe_hostname(hostname)
    if is_safe_literal is False:
        return None
    if is_safe_literal is True:
        return hostname

    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            ip_str = info[4][0]
            if _validate_ip(ip_str):
                return ip_str
            else:
                logger.warning(f"SSRF Protection: Blocked access to resolved private IP: {hostname} -> {ip_str}")
        return None
    except socket.gaierror:
        logger.warning(f"SSRF Protection: DNS resolution failed for {hostname}")
        return None
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return None

class SafeAsyncClient(httpx.AsyncClient):
    async def _send_single_request(self, request: httpx.Request) -> httpx.Response:
        # Override _send_single_request to intercept every request in the chain (including redirects)
        # And mitigate TOCTOU by resolving DNS first and rewriting URL to use IP.

        original_url = request.url
        hostname = original_url.host
        scheme = original_url.scheme

        # Resolve and validate
        safe_ip = await resolve_and_validate_async(hostname)
        if not safe_ip:
             raise httpx.RequestError(f"SSRF Protection: Access to {hostname} is blocked.")

        is_ip_literal = (safe_ip == hostname)

        if not is_ip_literal:
            # Rewrite URL to use IP to prevent TOCTOU
            new_url = original_url.copy_with(host=safe_ip)
            request.url = new_url

            # Set Host header if not present
            if "host" not in request.headers:
                request.headers["host"] = hostname

            # Set SNI for HTTPS
            if scheme == "https":
                request.extensions["sni_hostname"] = hostname

        return await super()._send_single_request(request)

class SafeClient(httpx.Client):
    def _send_single_request(self, request: httpx.Request) -> httpx.Response:
        original_url = request.url
        hostname = original_url.host
        scheme = original_url.scheme

        safe_ip = resolve_and_validate_sync(hostname)
        if not safe_ip:
             raise httpx.RequestError(f"SSRF Protection: Access to {hostname} is blocked.")

        is_ip_literal = (safe_ip == hostname)

        if not is_ip_literal:
            new_url = original_url.copy_with(host=safe_ip)
            request.url = new_url

            if "host" not in request.headers:
                request.headers["host"] = hostname

            if scheme == "https":
                request.extensions["sni_hostname"] = hostname

        return super()._send_single_request(request)

# Mock module class to replace httpx
class SafeHTTPXModule:
    # Expose exceptions and constants from httpx
    RequestError = httpx.RequestError
    ConnectError = httpx.ConnectError
    HTTPStatusError = httpx.HTTPStatusError
    TimeoutException = httpx.TimeoutException
    NetworkError = httpx.NetworkError
    codes = httpx.codes
    USE_CLIENT_DEFAULT = httpx.USE_CLIENT_DEFAULT

    def __init__(self):
        # Expose classes
        self.AsyncClient = SafeAsyncClient
        self.Client = SafeClient

    def get(self, url, **kwargs):
        with SafeClient() as client:
            return client.get(url, **kwargs)

    def post(self, url, **kwargs):
        with SafeClient() as client:
            return client.post(url, **kwargs)

    def put(self, url, **kwargs):
        with SafeClient() as client:
            return client.put(url, **kwargs)

    def delete(self, url, **kwargs):
        with SafeClient() as client:
            return client.delete(url, **kwargs)

    def patch(self, url, **kwargs):
        with SafeClient() as client:
            return client.patch(url, **kwargs)

    def head(self, url, **kwargs):
        with SafeClient() as client:
            return client.head(url, **kwargs)

    def options(self, url, **kwargs):
        with SafeClient() as client:
            return client.options(url, **kwargs)

    def stream(self, method, url, **kwargs):
        return SafeClient().stream(method, url, **kwargs)
