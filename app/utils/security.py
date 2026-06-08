from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

from app.utils.errors import SecurityViolationError

BLOCKED_SCHEMES = {
    "file",
    "ftp",
    "gopher",
    "dict",
    "chrome",
    "chrome-extension",
    "data",
    "javascript",
}

BLOCKED_HOSTNAMES = {
    "localhost",
    "169.254.169.254",
}

BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_blocked_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    for network in BLOCKED_NETWORKS:
        if ip_obj in network:
            return True
    return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast


def resolve_host_ips(hostname: str) -> set[str]:
    addresses: set[str] = set()
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SecurityViolationError(f"Unable to resolve host: {hostname}") from exc

    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET:
            addresses.add(sockaddr[0])
        elif family == socket.AF_INET6:
            addresses.add(sockaddr[0])
    return addresses


def validate_safe_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SecurityViolationError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise SecurityViolationError("URL hostname is required.")

    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTNAMES:
        raise SecurityViolationError("Blocked host is not allowed.")

    try:
        ipaddress.ip_address(parsed.hostname)
    except ValueError:
        for ip in resolve_host_ips(parsed.hostname):
            if is_blocked_ip(ip):
                raise SecurityViolationError("URL resolves to a blocked IP address.")
    else:
        if is_blocked_ip(parsed.hostname):
            raise SecurityViolationError("Blocked IP address is not allowed.")

    return url


def validate_redirect_target(base_url: str, location: str) -> str:
    return validate_safe_url(urljoin(base_url, location))
