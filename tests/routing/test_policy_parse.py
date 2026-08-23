"""Tests for routing policy JSON parsing."""

from __future__ import annotations

from routing.policy_parse import parse_routing_policy_json


def test_parse_routing_policy_json_plain_object() -> None:
    policy = parse_routing_policy_json(
        """
        {
          "net_classifications": [
            {"net_name": "MOTOR_OUT", "classification": "high_current", "explain": "20 A"}
          ],
          "notes": "Keep motor path manual."
        }
        """
    )
    assert policy.notes == "Keep motor path manual."
    assert len(policy.net_classifications) == 1
    assert policy.net_classifications[0].classification == "high_current"


def test_parse_routing_policy_json_fenced() -> None:
    policy = parse_routing_policy_json(
        """Here is the policy:
```json
{
  "net_classifications": [
    {"net_name": "XTAL_IN", "classification": "clock", "explain": "Crystal"}
  ],
  "notes": ""
}
```
"""
    )
    assert policy.net_classifications[0].net_name == "XTAL_IN"
