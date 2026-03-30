## 1. Decision Maker

### Integration summary

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

### Endpoint shape

- SADE -> Decision Maker: `POST /decision-request`
- Decision Maker -> SADE: `POST /decision-result`

### Request contract

Suggested request example:

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "submitted_at": "2026-03-27T21:19:47Z",
  "entry_request_kind": "ENTRY",
  "request_time": "2026-03-09T17:55:00Z",
  "requested_entry_time": "2026-03-09T18:00:00Z",
  "requested_exit_time": "2026-03-09T19:00:00Z",
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "owner_id": "owner-001"
  },
  "uav_model": {
    "model_id": "model-001",
    "name": "DJI Mavic 3",
    "max_wind_tolerance": 22.5,
    "max_temp_f": 110.0,
    "min_temp_f": -10.0,
    "max_payload_cap_lbs": 5
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
    "window_start": "2026-03-09T18:00:00Z",
    "window_end": "2026-03-09T19:00:00Z",
    "max_wind_knots": 0.0,
    "max_gust_knots": 0.0,
    "min_temp_f": 0.0,
    "max_temp_f": 0.0,
    "precipitation_summary": "none",
    "visibility_min_nm": 0.0,
    "source": "NOOP_HARDCODED",
    "confidence": 0.0,
    "generated_at": "2026-03-09T18:00:00Z"
  },
  "test_overrides": {},
  "entry_request_history": []
}
```

`test_overrides` is only for local/dev testing with stubbed services. It is not part of the long-term production contract.

### `applicable_scopes`

`applicable_scopes` tells the Decision Maker why a claim or reputation row is relevant to the current evaluation:

- `["PILOT"]` means the evidence is about the pilot.
- `["UAV"]` means the evidence is about the drone.
- `["PILOT", "UAV"]` means one observed record is relevant to both.

This is meaningful decision context. A pilot-scoped record and a UAV-scoped record tell different stories, even if they came from the same underlying flight.

`applicable_scopes` explains why a row is relevant. It does not mean other fields disappear from the row. For example, a record with `["PILOT"]` may still include `drone_id`, telemetry, and weather context because those are part of the observed flight.

### Example `attestation_claims`

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
    "issued_at": "2026-03-01T10:00:00Z",
    "expires_at": "2027-03-01T10:00:00Z",
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
    "issued_at": "2026-03-01T10:00:00Z",
    "expires_at": null,
    "evidence_ref": "attestation:ATT-3",
    "signature_ref": null
  }
]
```

For the current target shape:

- each claim should include `requirement_id`
- each claim should include `applicable_scopes`
- claims should use `["PILOT"]` or `["UAV"]` in v1

### Example `reputation_records`

```json
"reputation_records": [
  {
    "reputation_record_id": "rep-001",
    "applicable_scopes": ["PILOT", "UAV"],
    "pilot_id": "pilot-001",
    "drone_id": "drone-001",
    "observed_at": "2026-03-02T18:32:00Z",
    "telemetry": {
      "altitude_min_m": 12.0,
      "altitude_max_m": 94.5,
      "battery_start_pct": 98.0,
      "battery_end_pct": 61.0,
      "battery_voltage_start_v": 16.2,
      "battery_voltage_end_v": 14.9
    },
    "weather_observed": {
      "max_wind_knots": 24.0,
      "max_gust_knots": 31.0,
      "visibility_min_nm": 8.0
    }
  },
  {
    "reputation_record_id": "rep-002",
    "applicable_scopes": ["PILOT"],
    "pilot_id": "pilot-001",
    "drone_id": "drone-777",
    "observed_at": "2026-02-01T14:12:00Z",
    "telemetry": {
      "altitude_min_m": 10.0,
      "altitude_max_m": 70.0,
      "battery_start_pct": 96.0,
      "battery_end_pct": 68.0,
      "battery_voltage_start_v": 16.1,
      "battery_voltage_end_v": 15.0
    },
    "weather_observed": {
      "max_wind_knots": 19.0,
      "max_gust_knots": 25.0,
      "visibility_min_nm": 9.0
    }
  },
  {
    "reputation_record_id": "rep-003",
    "applicable_scopes": ["UAV"],
    "pilot_id": "pilot-999",
    "drone_id": "drone-001",
    "observed_at": "2026-01-12T09:40:00Z",
    "telemetry": {
      "altitude_min_m": 8.0,
      "altitude_max_m": 82.0,
      "battery_start_pct": 97.0,
      "battery_end_pct": 66.0,
      "battery_voltage_start_v": 16.0,
      "battery_voltage_end_v": 14.8
    },
    "weather_observed": {
      "max_wind_knots": 22.0,
      "max_gust_knots": 28.0,
      "visibility_min_nm": 7.0
    }
  }
]
```

For the current target shape:

- reputation should be sent as one outward list
- rows should be deduplicated by `reputation_record_id`
- each row should include `applicable_scopes`
- zone should be treated as context, not as a reusable scope

### Example `entry_request_history`

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

### Example `test_overrides` for dev testing only

This is not part of the long-term production contract.

```json
"test_overrides": {
  "decision_maker": {
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
  },
  "weather_service": {
    "forecast": {
      "sade_zone_id": "zone-001",
      "window_start": "2026-03-09T18:00:00Z",
      "window_end": "2026-03-09T19:00:00Z",
      "max_wind_knots": 18.0,
      "max_gust_knots": 24.0,
      "min_temp_f": 42.0,
      "max_temp_f": 47.0,
      "precipitation_summary": "none",
      "visibility_min_nm": 8.0,
      "source": "TEST_OVERRIDE",
      "confidence": 1.0,
      "generated_at": "2026-03-09T17:55:00Z"
    }
  }
}
```

### Immediate response

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

### Result callback contract

SADE returns `200 OK` once the callback has been durably accepted.

#### Approved

```json
{
  "evaluation_id": "b80eac98-e26b-4988-9179-c4e84fc4530f",
  "evaluation_series_id": "f17f4eab-35e6-4d2a-a802-1e00e51ade3d",
  "completed_at": "2026-03-27T21:19:48Z",
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
  "completed_at": "2026-03-27T21:19:48Z",
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
  "completed_at": "2026-03-27T21:19:48Z",
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
  "completed_at": "2026-03-27T21:19:48Z",
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
  "completed_at": "2026-03-27T21:19:48Z",
  "processing_failed": true,
  "reason": "Decision Maker could not process this evaluation."
}
```

For v1, SADE does not expect intermediate progress callbacks.

### Standardized `evidence_requirement_spec` for `ACTION_REQUIRED`

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
