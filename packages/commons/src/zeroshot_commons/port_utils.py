from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortStatus:
    port: int
    is_open: bool


@dataclass(frozen=True, slots=True)
class PortConfig:
    min_port: int
    max_port: int


async def find_open_port(config: PortConfig) -> int:
    if config.min_port > config.max_port:
        raise ValueError("min_port must be less than or equal to max_port")

    for port in range(config.min_port, config.max_port + 1):
        result = await check_port(port)
        if result.is_open:
            return result.port

    raise RuntimeError("No open port found in the specified range")


async def check_port(port: int) -> PortStatus:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", port))
        except OSError:
            return PortStatus(port=port, is_open=False)
        return PortStatus(port=port, is_open=True)
