#!/usr/bin/env python3
"""Small deny-by-default evaluator for the identity/network study lab."""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
from typing import Any


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scope_contains(assignment_scope: str, resource_scope: str) -> bool:
    parent = assignment_scope.rstrip("/")
    child = resource_scope.rstrip("/")
    return child == parent or child.startswith(parent + "/")


def identity_allowed(
    policy: dict[str, Any], principal: str, action: str, resource_scope: str
) -> bool:
    for assignment in policy["role_assignments"]:
        if assignment["principal"] != principal:
            continue
        actions = policy["roles"].get(assignment["role"], [])
        if action in actions and scope_contains(assignment["scope"], resource_scope):
            return True
    return False


def flow_allowed(
    policy: dict[str, Any], source_ip: str, destination_ip: str, protocol: str, port: int
) -> bool:
    source = ipaddress.ip_address(source_ip)
    destination = ipaddress.ip_address(destination_ip)
    for flow in policy["network_flows"]:
        if (
            source in ipaddress.ip_network(flow["source"])
            and destination in ipaddress.ip_network(flow["destination"])
            and protocol.lower() == flow["protocol"]
            and port == flow["port"]
        ):
            return True
    return False
