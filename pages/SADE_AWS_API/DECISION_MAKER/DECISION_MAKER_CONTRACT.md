# Decision Maker Contract

**Last Updated On:** 2026-04-22

Unless noted otherwise, quantities, timestamps, and coordinate conventions follow [../QUANTITIES_AND_UNITS.md](../QUANTITIES_AND_UNITS.md).

## Integration Summary

- SADE sends one decision job at a time to `POST /decision-request`.
- The Decision Maker should immediately acknowledge acceptance with `202 Accepted`.
- The Decision Maker later returns one final result to SADE by calling `POST /decision-result`.
- `evaluation_id` is the idempotency and correlation key for one specific decision job.
- `evaluation_series_id` groups related evaluations in the same broader workflow, such as an initial request and a later retry.

For v1, the Decision Maker should produce exactly one final callback per `evaluation_id`:

- `APPROVED`
- `APPROVED_CONSTRAINTS`
- `ACTION_REQUIRED`
- `DENIED`
- or a catch-all processing failure

## Endpoint Shape

- SADE -> Decision Maker: `POST /decision-request`
- Decision Maker -> SADE: `POST /decision-result`

## Request Contract

Suggested request example:

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "submitted_at_utc": "2026-03-27T21:19:47Z",
  "entry_request_kind": "ENTRY",
  "request_time_utc": "2026-03-09T17:55:00Z",
  "requested_entry_time_utc": "2026-03-09T18:00:00Z",
  "requested_exit_time_utc": "2026-03-09T19:00:00Z",
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "organization_id": "org-001"
  },
  "uav_model": {
    "model_id": "model-001",
    "name": "DJI Mavic 3",
    "max_wind_tolerance_knots": 22.5,
    "max_temp_f": 110.0,
    "min_temp_f": -10.0,
    "max_payload_cap_kg": 5
  },
  "pilot": {
    "pilot_id": "pilot-001",
    "organization_id": "org-001"
  },
  "zone": {
    "sade_zone_id": "zone-001",
    "name": "Zone 001"
  },
  "attestation_claims": [],
  "reputation_records": [],
  "weather_forecast": {
    "sade_zone_id": "zone-001",
    "window_start_utc": "2026-03-09T18:00:00Z",
    "window_end_utc": "2026-03-09T19:00:00Z",
    "max_wind_knots": 0.0,
    "max_gust_knots": 0.0,
    "min_temp_f": 0.0,
    "max_temp_f": 0.0,
    "precipitation_summary": "none",
    "visibility_min_nm": 0.0,
    "source": "NOOP_HARDCODED",
    "confidence_ratio": 0.0,
    "generated_at_utc": "2026-03-09T18:00:00Z"
  },
  "test_overrides": null,
  "entry_request_history": []
}
```

`test_overrides` is only for local/dev testing with the temporary Decision Maker stub. It is not part of the long-term production contract.

For the outbound Decision Maker contract, `test_overrides` is nullable and only carries Decision Maker-specific stub instructions. Weather overrides are resolved inside SADE and reflected through `weather_forecast`, not forwarded here.

## `applicable_scopes`

`applicable_scopes` tells the Decision Maker why a claim or reputation row is relevant to the current evaluation:

- `["PILOT"]` means the evidence is about the pilot.
- `["UAV"]` means the evidence is about the drone.
- `["PILOT", "UAV"]` means one observed record is relevant to both.

This is meaningful decision context. A pilot-scoped record and a UAV-scoped record tell different stories, even if they came from the same underlying flight.

`applicable_scopes` explains why a row is relevant. It does not mean other fields disappear from the row. For example, a record with `["PILOT"]` may still include `drone_id`, telemetry, and weather context because those are part of the observed flight.

## Example `attestation_claims`

```json
"attestation_claims": [
  {
    "requirement_id": "req-part-107",
    "category": "CERTIFICATION",
    "expr": "PART_107",
    "keyword": "PART_107",
    "status": "SATISFIED",
    "params": [],
    "applicable_scopes": ["PILOT"],
    "meta": {
      "status": "SATISFIED"
    },
    "issued_at_utc": "2026-03-01T10:00:00Z",
    "expires_at_utc": "2027-03-01T10:00:00Z",
    "evidence_ref": "attestation:ATT-2",
    "signature_ref": null
  },
  {
    "requirement_id": "req-max-wind-gust",
    "category": "ENVIRONMENT",
    "expr": "MAX_WIND_GUST(28mph)",
    "keyword": "MAX_WIND_GUST",
    "status": "SATISFIED",
    "params": [
      "28mph"
    ],
    "applicable_scopes": ["UAV"],
    "meta": {
      "status": "SATISFIED",
      "observed_max_wind_gust": "24mph"
    },
    "issued_at_utc": "2026-03-01T10:00:00Z",
    "expires_at_utc": null,
    "evidence_ref": "attestation:ATT-3",
    "signature_ref": null
  }
]
```

For the current target shape:

- each claim should include `requirement_id`
- each claim should include `applicable_scopes`
- claims should use `["PILOT"]` or `["UAV"]` in v1

## Example `reputation_records`

```json
"reputation_records": [
  {
    "reputation_record_id": "rep-001",
    "applicable_scopes": ["PILOT", "UAV"],
    "evaluation_series_id": "series-001",
    "pilot_id": "pilot-001",
    "drone_id": "drone-001",
    "flight_session_id": "flight-session-001",
    "organization_id": "org-001",
    "sade_zone_id": "zone-001",
    "telemetry_summary": {
      "altitude_min_m": 12.0,
      "altitude_max_m": 94.5,
      "distance_flown_m": 2896.8
    },
    "declared_payload": {
      "total_weight_kg": 2.5,
      "components": [
        {
          "type": "CAMERA_01"
        }
      ]
    },
    "weather_observed": {
      "window_start_utc": "2026-03-02T18:00:00Z",
      "window_end_utc": "2026-03-02T18:32:00Z",
      "max_wind_knots": 24.0,
      "max_gust_knots": 31.0,
      "visibility_min_nm": 8.0
    },
    "events": [
      {
        "type": "FLIGHT_SEGMENT",
        "time_in_utc": "2026-03-02T18:00:00Z",
        "time_out_utc": "2026-03-02T18:32:00Z"
      }
    ]
  },
  {
    "reputation_record_id": "rep-002",
    "applicable_scopes": ["PILOT"],
    "evaluation_series_id": "series-002",
    "pilot_id": "pilot-001",
    "drone_id": "drone-777",
    "flight_session_id": "flight-session-002",
    "organization_id": "org-001",
    "sade_zone_id": "zone-002",
    "telemetry_summary": {
      "altitude_min_m": 10.0,
      "altitude_max_m": 70.0,
      "distance_flown_m": 1600.0
    },
    "declared_payload": {},
    "weather_observed": {
      "window_start_utc": "2026-02-01T13:45:00Z",
      "window_end_utc": "2026-02-01T14:12:00Z",
      "max_wind_knots": 19.0,
      "max_gust_knots": 25.0,
      "visibility_min_nm": 9.0
    },
    "events": [
      {
        "type": "FLIGHT_SEGMENT",
        "time_in_utc": "2026-02-01T13:45:00Z",
        "time_out_utc": "2026-02-01T14:12:00Z"
      }
    ]
  },
  {
    "reputation_record_id": "rep-003",
    "applicable_scopes": ["UAV"],
    "evaluation_series_id": "series-003",
    "pilot_id": "pilot-999",
    "drone_id": "drone-001",
    "flight_session_id": "flight-session-003",
    "organization_id": "org-999",
    "sade_zone_id": "zone-003",
    "telemetry_summary": {
      "altitude_min_m": 8.0,
      "altitude_max_m": 82.0,
      "distance_flown_m": 1900.0
    },
    "declared_payload": {},
    "weather_observed": {
      "window_start_utc": "2026-01-12T09:05:00Z",
      "window_end_utc": "2026-01-12T09:40:00Z",
      "max_wind_knots": 22.0,
      "max_gust_knots": 28.0,
      "visibility_min_nm": 7.0
    },
    "events": [
      {
        "type": "FLIGHT_SEGMENT",
        "time_in_utc": "2026-01-12T09:05:00Z",
        "time_out_utc": "2026-01-12T09:40:00Z"
      }
    ]
  }
]
```

For the current target shape:

- reputation should be sent as one outward list
- rows should be deduplicated by `reputation_record_id`
- each row should include `applicable_scopes`
- each row should carry the richer `telemetry_summary`, `declared_payload`, `weather_observed`, and `events` objects when available
- zone should be treated as context, not as a reusable scope
- event, incident-code, and payload-type conventions follow [../FLIGHT_MONITOR/REFERENCE_TABLES.md](../FLIGHT_MONITOR/REFERENCE_TABLES.md)

## Example `entry_request_history`

`entry_request_history` summarizes prior decisions that are relevant to the current evaluation.

```json
"entry_request_history": [
  {
    "entry_request_kind": "ENTRY",
    "decision": "ACTION_REQUIRED",
    "decision_reason": "Additional evidence required.",
    "decision_output": {
      "decision": "ACTION_REQUIRED",
      "reason": "Additional evidence required.",
      "constraints": [],
      "evidence_requirement_spec": {
        "type": "EVIDENCE_REQUIREMENT",
        "request_id": "27102df7-0afb-4dd6-9228-a91e87391dc0",
        "spec_version": "1.0",
        "categories": [
          {
            "category": "CERTIFICATION",
            "requirements": [
              {
                "requirement_id": "req-part-107",
                "expr": "PART_107",
                "keyword": "PART_107",
                "params": [],
                "applicable_scopes": ["PILOT"]
              }
            ]
          }
        ]
      }
    }
  }
]
```

## Example `test_overrides` for dev testing only

This is not part of the long-term production contract.

```json
"test_overrides": {
  "force_decision": "ACTION_REQUIRED",
  "evidence_requirement_spec": {
    "categories": [
      {
        "category": "CUSTOM_CATEGORY",
        "requirements": [
          {
            "requirement_id": "req-special-review",
            "expr": "SPECIAL_REVIEW",
            "keyword": "SPECIAL_REVIEW",
            "params": [],
            "applicable_scopes": ["PILOT"]
          }
        ]
      }
    ]
  }
}
```

## Immediate Response

The immediate response should only indicate whether the Decision Maker accepted the work item for asynchronous processing.

Suggested response:

```json
{
  "status": "ACCEPTED",
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d"
}
```

Recommended HTTP behavior:

- `202 Accepted` for normal acceptance
- `200 OK` is also acceptable for an idempotent duplicate of the same `evaluation_id`
- `400 Bad Request` for invalid payloads
- `401 Unauthorized` or `403 Forbidden` for auth problems
- `404 Not Found` for routing/configuration mistakes

SADE retries transport failures, `429`, and `5xx` responses.

## Result Callback Contract

SADE returns `200 OK` once the callback has been durably accepted.

#### Approved

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at_utc": "2026-03-27T21:19:48Z",
  "result": {
    "decision": "APPROVED",
    "reason": "Mission is approved under current conditions.",
    "constraints": [],
    "evidence_requirement_spec": null
  }
}
```

#### Approved with constraints

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at_utc": "2026-03-27T21:19:48Z",
  "result": {
    "decision": "APPROVED_CONSTRAINTS",
    "reason": "Mission is approved with additional operating constraints.",
    "constraints": [
      {
        "code": "MAX_ALTITUDE_M",
        "value": 90
      },
      {
        "code": "DAYLIGHT_ONLY",
        "value": true
      }
    ],
    "evidence_requirement_spec": null
  }
}
```

#### Action required

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at_utc": "2026-03-27T21:19:48Z",
  "result": {
    "decision": "ACTION_REQUIRED",
    "reason": "Additional evidence is required before approval.",
    "constraints": [],
    "evidence_requirement_spec": {
      "type": "EVIDENCE_REQUIREMENT",
      "spec_version": "1.0",
      "request_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
      "subject": {
        "sade_zone_id": "zone-001",
        "pilot_id": "pilot-001",
        "organization_id": "org-001",
        "drone_id": "drone-001"
      },
      "categories": [
        {
          "category": "CERTIFICATION",
          "requirements": [
            {
              "requirement_id": "req-part-107",
              "expr": "PART_107",
              "keyword": "PART_107",
              "params": [],
              "applicable_scopes": ["PILOT"]
            }
          ]
        }
      ]
    }
  }
}
```

#### Denied

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at_utc": "2026-03-27T21:19:48Z",
  "result": {
    "decision": "DENIED",
    "reason": "Mission is not permitted under current policy and conditions.",
    "constraints": [],
    "evidence_requirement_spec": null
  }
}
```

#### Catch-all processing failure

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at_utc": "2026-03-27T21:19:48Z",
  "processing_failed": true,
  "reason": "Decision Maker could not process this evaluation."
}
```

For v1, SADE does not expect intermediate progress callbacks.

## Standardized `evidence_requirement_spec` for `ACTION_REQUIRED`

When the Decision Maker returns `ACTION_REQUIRED`, it should produce a standardized `evidence_requirement_spec`.

That spec tells SADE:

- what additional evidence is being requested
- which subject each requirement applies to
- which `requirement_id` should later appear on resulting claims

Suggested shape:

```json
{
  "type": "EVIDENCE_REQUIREMENT",
  "spec_version": "1.0",
  "request_id": "REQ-0001",
  "subject": {
    "sade_zone_id": "ZONE-123",
    "pilot_id": "PILOT-456",
    "organization_id": "ORG-789",
    "drone_id": "DRONE-001"
  },
  "categories": [
    {
      "category": "CERTIFICATION",
      "requirements": [
        {
          "requirement_id": "req-part-107",
          "expr": "PART_107",
          "keyword": "PART_107",
          "params": [],
          "applicable_scopes": ["PILOT"]
        },
        {
          "requirement_id": "req-bvlos-faa",
          "expr": "BVLOS(FAA)",
          "keyword": "BVLOS",
          "params": ["FAA"],
          "applicable_scopes": ["PILOT"]
        }
      ]
    },
    {
      "category": "CAPABILITY",
      "requirements": [
        {
          "requirement_id": "req-night-position-lights",
          "expr": "NIGHT_POSITION_LIGHTS",
          "keyword": "NIGHT_POSITION_LIGHTS",
          "params": [],
          "applicable_scopes": ["UAV"]
        },
        {
          "requirement_id": "req-payload-weight",
          "expr": "PAYLOAD(weight<=2kg)",
          "keyword": "PAYLOAD",
          "params": [{ "key": "weight", "value": "<=2kg" }],
          "applicable_scopes": ["UAV"]
        }
      ]
    },
    {
      "category": "ENVIRONMENT",
      "requirements": [
        {
          "requirement_id": "req-max-wind-gust",
          "expr": "MAX_WIND_GUST(28mph)",
          "keyword": "MAX_WIND_GUST",
          "params": ["28mph"],
          "applicable_scopes": ["UAV"]
        }
      ]
    }
  ]
}
```
