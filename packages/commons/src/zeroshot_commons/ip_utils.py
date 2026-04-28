from __future__ import annotations

import ipaddress


def parse_ip_address_from_x_forwarded_for(
    ip_address_from_x_forwarded_for: str | None = None,
) -> str | None:
    if ip_address_from_x_forwarded_for is None:
        return None
    maybe_ip_address = ip_address_from_x_forwarded_for.split(",")[0].strip()
    return maybe_ip_address if is_valid_ip_address(maybe_ip_address) else None


def is_valid_ip_address(ip_address: str) -> bool:
    if not ip_address:
        return False
    try:
        ipaddress.IPv4Address(ip_address)
    except ipaddress.AddressValueError:
        return False
    return True


def is_valid_ip_cidr_block(cidr_block: str) -> bool:
    if not cidr_block:
        return False
    try:
        ip_part, prefix_part = cidr_block.split("/", 1)
        prefix = int(prefix_part)
    except (TypeError, ValueError):
        return False
    return is_valid_ip_address(ip_part) and 0 <= prefix <= 32


def is_ip_in_cidr_block(ip_address: str, cidr_block: str) -> bool:
    if not is_valid_ip_address(ip_address) or not is_valid_ip_cidr_block(cidr_block):
        return False
    return ipaddress.IPv4Address(ip_address) in ipaddress.IPv4Network(cidr_block, strict=False)
