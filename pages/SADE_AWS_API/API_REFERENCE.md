# SADE Client API Reference (AWS)

**Last Updated On:** 2026-04-22

This is the client-facing API contract for teams integrating with the deployed SADE AWS runtime.

Quantities, units, timestamp format, and coordinate conventions follow [./QUANTITIES_AND_UNITS.md](./QUANTITIES_AND_UNITS.md).

## Base URL

`http://sarec-sade-use2-api-alb-1413405053.us-east-2.elb.amazonaws.com`

## Common rules

1. `POST` endpoints require `Content-Type: application/json`.
2. Workflow `POST` endpoints require `idempotency_key`, except `POST /exit-request` and `POST /tracker-session-finalized`, which deduplicate by `flight_session_id`.
3. Async workflow `POST` endpoints return an acknowledgment first, not the final business outcome.
4. `POST /entry-request` and `POST /attestation-submission` return `RequestReceipt` with HTTP `202` on acceptance.
5. `POST /exit-request` returns an async acknowledgment with HTTP `202` on acceptance.
6. `POST /tracker-session-finalized` remains synchronous and returns its final result contract.
7. Validation/transport errors use HTTP `400` or `500`.

This async design is deliberate.

`POST /entry-request` is not modeled as a synchronous decision RPC because two stages in the workflow can vary significantly in runtime:

1. The decision adapter itself may take time. In realistic deployments this may involve an LLM or another external reasoning component, which can be slow or variable under load.
2. The workflow may become `ACTION_REQUIRED`, which introduces an attestation step. If the required evidence is not already on record, a human-in-the-loop process is needed before SafeCert can respond.

If SADE tried to keep the original HTTP request open across those stages, the system would be exposed to:

1. client-side timeout behavior
2. load balancer and gateway timeout limits
3. dropped long-lived connections
4. retry duplication under slow downstream dependencies
5. poor operator UX because some requests would return quickly and others would appear to hang

The chosen contract is therefore:

1. accept or reject the request quickly
2. return a `status_url`
3. let the workflow continue asynchronously and event-driven inside SADE
4. let operators check that URL directly, or view the same information in a UI

Registry and status-query endpoints still use the standard HTTP error envelope:

```json
{
  "error": {
    "reason": "..."
  }
}
```

## Quick terminology

1. `UAV model`: the drone type/spec capabilities (for example wind tolerance and temperature limits).
2. `UAV`: a specific drone unit that references one `uav-model`.
3. `Pilot`: the operator identity and organization.
4. `UAV organization`: the organization that owns or controls a specific UAV record.
5. `Zone`: the SADE-managed flight area (polygon_geojson + altitude ceiling).
6. `Upsert`: create the record if it does not exist, or update it if it already exists.

## Route list

- `GET /health`: service liveness check.
- `POST /entry-request`: submit an entry workflow for async processing.
- `GET /entry-requests/{evaluation_series_id}`: fetch authoritative entry workflow status.
- `POST /exit-request`: record operator intent to leave early and queue Flight Monitor delivery.
- `POST /attestation-submission`: submit attestation evidence for an open action.
- `GET /actions/{action_id}`: fetch authoritative action-required status.
- `POST /tracker-session-finalized`: finalize a flight session from tracker telemetry.
- `GET /reputation-records`: list stored reputation records filtered by organization, pilot, and/or UAV.
- `GET /attestation-claims`: list stored attestation claims filtered by organization, pilot, and/or UAV.
- `POST /testing/reputation-records`: create a synthetic reputation record for testing/scenario seeding.
- `POST /testing/attestation-claims`: create synthetic attestation claims for testing/scenario seeding.
- `POST /registry/uav-model`: create or update one UAV model.
- `POST /registry/uav`: create or update one UAV.
- `POST /registry/pilot`: create or update one pilot.
- `POST /registry/zone`: create or update one zone.
- `GET /registry/uav-models`: list all UAV models.
- `GET /registry/uavs`: list UAVs, optionally filtered by organization.
- `GET /registry/pilots`: list pilots, optionally filtered by organization.
- `GET /registry/zones`: list all zones.
- `GET /registry/uav-model/{model_id}`: fetch one UAV model by id.
- `GET /registry/uav/{drone_id}`: fetch one UAV by id.
- `GET /registry/pilot/{pilot_id}`: fetch one pilot by id.
- `GET /registry/zone/{sade_zone_id}`: fetch one zone by id.
- `DELETE /registry/uav-model/{model_id}`: delete one UAV model if unused.
- `DELETE /registry/uav/{drone_id}`: delete one UAV if no active workflow depends on it.
- `DELETE /registry/pilot/{pilot_id}`: delete one pilot if no active workflow depends on it.
- `DELETE /registry/zone/{sade_zone_id}`: delete one zone if no active workflow depends on it.

## Supported filters

- `GET /registry/pilots?organization_id=org-001`: limit pilots to one organization.
- `GET /registry/uavs?organization_id=org-001`: limit UAVs to one organization.
- `GET /registry/uavs?include_model=true`: embed each UAV's resolved model payload.
- `GET /registry/uavs?organization_id=org-001&include_model=true`: combine both UAV filters in one request.
- `GET /reputation-records?organization_id=org-001`: limit reputation records to one organization.
- `GET /reputation-records?pilot_id=pilot-001&drone_id=drone-001`: combine reputation filters with AND semantics.
- `GET /attestation-claims?organization_id=org-001`: limit claims to one organization.
- `GET /attestation-claims?pilot_id=pilot-001`: limit claims to one pilot-bound subject.

## Registry API

The registry is the required reference data layer.  
Create these records first, then use workflow routes like `/entry-request`.

### `POST /registry/uav-model`

Registers a UAV model in SADE.  
Uses upsert behavior by `model_id`.

Request and response example

Request:

```json
{
  "model_id": "model-001",
  "name": "DJI Mavic 3",
  "max_wind_tolerance_knots": 22.5,
  "max_payload_cap_kg": 5,
  "max_temp_f": 110.0,
  "min_temp_f": -10.0
}
```

Response:

```json
{
  "status": "UPSERTED",
  "uav_model": {
    "model_id": "model-001",
    "name": "DJI Mavic 3",
    "max_wind_tolerance_knots": 22.5,
    "max_payload_cap_kg": 5,
    "max_temp_f": 110.0,
    "min_temp_f": -10.0
  }
}
```



### `POST /registry/uav`

Registers a specific UAV (drone) and links it to its `model_id`.  
Uses upsert behavior by `drone_id`.

Entry workflows require the UAV's `organization_id` to match the pilot's `organization_id`.

Request and response example

Request:

```json
{
  "drone_id": "drone-001",
  "model_id": "model-001",
  "organization_id": "org-001"
}
```

Response:

```json
{
  "status": "UPSERTED",
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "organization_id": "org-001"
  }
}
```



### `POST /registry/pilot`

Registers a pilot identity used in entry and attestation workflows.  
Uses upsert behavior by `pilot_id`.

Request and response example

Request:

```json
{
  "pilot_id": "pilot-001",
  "organization_id": "org-001"
}
```

Response:

```json
{
  "status": "UPSERTED",
  "pilot": {
    "pilot_id": "pilot-001",
    "organization_id": "org-001"
  }
}
```



### `POST /registry/zone`

Registers a SADE zone boundary and altitude policy.  
Uses upsert behavior by `sade_zone_id`.

Request and response example

Request:

```json
{
  "sade_zone_id": "zone-001",
  "name": "Zone 001",
  "polygon_geojson": {
    "type": "Polygon",
    "coordinates": [
      [
        [-86.0, 41.7],
        [-86.1, 41.7],
        [-86.1, 41.8],
        [-86.0, 41.8],
        [-86.0, 41.7]
      ]
    ]
  },
  "altitude_ceiling_m": 120.0
}
```

Response:

```json
{
  "status": "UPSERTED",
  "zone": {
    "sade_zone_id": "zone-001",
    "name": "Zone 001",
    "polygon_geojson": {
      "type": "Polygon",
      "coordinates": [
        [
          [-86.0, 41.7],
          [-86.1, 41.7],
          [-86.1, 41.8],
          [-86.0, 41.8],
          [-86.0, 41.7]
        ]
      ]
    },
    "altitude_ceiling_m": 120.0
  }
}
```



### Registry GET endpoints

- `GET /registry/uav-model/{model_id}`
- `GET /registry/uav/{drone_id}`
- `GET /registry/pilot/{pilot_id}`
- `GET /registry/zone/{sade_zone_id}`

Fetches one registry record by id.  
Returns HTTP `404` if the record does not exist.

GET response examples

Example `GET /registry/uav/drone-001`:

```json
{
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "organization_id": "org-001"
  }
}
```

Not found example (HTTP 404):

```json
{
  "error": {
    "reason": "UAV not found: drone-999"
  }
}
```



### Registry collection endpoints

- `GET /registry/uav-models`
- `GET /registry/uavs`
- `GET /registry/pilots`
- `GET /registry/zones`

Fetches full registry collections.

Supported filters:

- `GET /registry/uavs?organization_id=org-001`
- `GET /registry/uavs?organization_id=org-001&include_model=true`
- `GET /registry/pilots?organization_id=org-001`

Zones and UAV models are currently global and do not support organization filtering.

Collection response examples

Example `GET /registry/uavs?organization_id=org-001&include_model=true`:

```json
{
  "uavs": [
    {
      "drone_id": "drone-001",
      "model_id": "model-001",
      "organization_id": "org-001",
      "uav_model": {
        "model_id": "model-001",
        "name": "DJI Mavic 3",
        "max_wind_tolerance_knots": 22.5,
        "max_payload_cap_kg": 5,
        "max_temp_f": 110.0,
        "min_temp_f": -10.0
      }
    }
  ]
}
```

Example `GET /registry/pilots?organization_id=org-001`:

```json
{
  "pilots": [
    {
      "pilot_id": "pilot-001",
      "organization_id": "org-001"
    }
  ]
}
```



### Registry delete endpoints

- `DELETE /registry/uav-model/{model_id}`
- `DELETE /registry/uav/{drone_id}`
- `DELETE /registry/pilot/{pilot_id}`
- `DELETE /registry/zone/{sade_zone_id}`

Deletes one registry record by id.

Delete guard behavior:

- returns HTTP `404` if the record does not exist
- returns HTTP `409` if deleting the record would break active workflow state
- `DELETE /registry/uav-model/{model_id}` also returns HTTP `409` if any UAV still references that model

Delete response examples

Successful delete:

```json
{
  "status": "DELETED",
  "zone": {
    "sade_zone_id": "zone-002",
    "name": "Unused Zone",
    "polygon_geojson": {
      "type": "Polygon",
      "coordinates": []
    },
    "altitude_ceiling_m": 50.0
  }
}
```

Blocked delete (HTTP 409):

```json
{
  "error": {
    "reason": "Cannot delete UAV referenced by active workflows or planned sessions: drone-001"
  }
}
```



## Operator APIs

### `GET /health`

Light service liveness check used by humans, scripts, and load balancer health checks.

Response example

```json
{
  "status": "ok",
  "mode": "prod"
}
```



### `POST /entry-request`

Requests authorization for a UAV + pilot to enter a specific zone for a time window.  
This is now an asynchronous command endpoint.  
It returns a receipt, not the final decision body.

This is intentional, not temporary. The endpoint acknowledges durable workflow acceptance first, then the caller follows the returned `status_url` for progress and outcome.

Business validation note:

- SADE rejects the request if `pilot.organization_id` and `uav.organization_id` do not match.

Request example

```json
{
  "idempotency_key": "a8d87030-f7ea-4301-b03a-9de4f843c5fe",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "sade_zone_id": "zone-001",
  "organization_id": "org-001",
  "notifications": {
    "entry_request_updates": {
      "enabled": true,
      "transport": "MQTT"
    }
  },
  "requested_entry_time_utc": "2026-03-09T18:00:00Z",
  "requested_exit_time_utc": "2026-03-09T19:00:00Z",
  "request_time_utc": "2026-03-09T17:55:00Z",
  "declared_payload": {
    "total_weight_kg": 2.5,
    "components": [
      {
        "type": "CAMERA_01"
      }
    ]
  },
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  },
  "test_overrides": {
    "decision_maker": {
      "force_decision": "ACTION_REQUIRED"
    },
    "weather_service": {
      "forecast": {
        "sade_zone_id": "zone-001",
        "window_start_utc": "2026-03-09T18:00:00Z",
        "window_end_utc": "2026-03-09T19:00:00Z",
        "max_wind_knots": 18.0,
        "max_gust_knots": 24.0,
        "min_temp_f": 42.0,
        "max_temp_f": 47.0,
        "precipitation_summary": "none",
        "visibility_min_nm": 8.0,
        "source": "TEST_OVERRIDE",
        "confidence_ratio": 1.0,
        "generated_at_utc": "2026-03-09T17:55:00Z"
      }
    },
    "flight_monitor": {
      "mode": "SIMULATE_FINALIZATION",
      "telemetry_summary": {
        "altitude_max_m": 88.0,
        "battery_end_pct": 61.0
      },
      "events": [
        {
          "type": "FLIGHT_SEGMENT",
          "time_in_utc": "2026-03-09T18:05:00Z",
          "time_out_utc": "2026-03-09T18:41:00Z"
        }
      ]
    }
  }
}
```

Optional test-only override hook (inside top-level `test_overrides`):

- `decision_maker.force_decision`: `APPROVED`, `APPROVED_CONSTRAINTS`, `DENIED`, `ACTION_REQUIRED`, `NONE`, `RAISE`
- `decision_maker.evidence_requirement_spec`: optional requirement override for forced `ACTION_REQUIRED` stub responses
- `weather_service.forecast`: temporary override payload consumed by the no-op environmental service in local/dev flows
- `flight_monitor`: optional temporary pass-through object forwarded as the outbound Flight Monitor `test_overrides` value for stub/dev behavior

Example override shape:

```json
{
  "test_overrides": {
    "decision_maker": {
      "force_decision": "ACTION_REQUIRED",
      "evidence_requirement_spec": {
        "categories": [
          {
            "category": "CUSTOM_CATEGORY",
            "requirements": [
              {
                "expr": "SPECIAL_REVIEW",
                "keyword": "SPECIAL_REVIEW",
                "params": []
              }
            ]
          }
        ]
      }
    },
    "weather_service": {
      "forecast": {
        "sade_zone_id": "zone-001",
        "window_start_utc": "2026-03-09T18:00:00Z",
        "window_end_utc": "2026-03-09T19:00:00Z",
        "max_wind_knots": 18.0,
        "max_gust_knots": 24.0,
        "min_temp_f": 42.0,
        "max_temp_f": 47.0,
        "precipitation_summary": "none",
        "visibility_min_nm": 8.0,
        "source": "TEST_OVERRIDE",
        "confidence_ratio": 1.0,
        "generated_at_utc": "2026-03-09T17:55:00Z"
      }
    },
    "flight_monitor": {
      "mode": "SIMULATE_FINALIZATION",
      "telemetry_summary": {
        "altitude_max_m": 88.0,
        "battery_end_pct": 61.0
      },
      "events": [
        {
          "type": "FLIGHT_SEGMENT",
          "time_in_utc": "2026-03-09T18:05:00Z",
          "time_out_utc": "2026-03-09T18:41:00Z"
        }
      ]
    }
  },
  "declared_payload": {
    "total_weight_kg": 2.5,
    "components": [
      {
        "type": "CAMERA_01"
      }
    ]
  },
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  }
}
```

This is a testing hook for the temporary stubbed integrations. It is useful when the SafeCert or Decision Maker teams want to exercise deterministic paths without changing SADE code.

When `decision_maker.force_decision` is `ACTION_REQUIRED`, you may provide `decision_maker.evidence_requirement_spec.categories` to override the stub's default requirement categories for SafeCert testing.

Optional notifications:

- include `notifications.entry_request_updates.enabled=true` to request MQTT workflow notifications
- when accepted, SADE returns the derived topic in the receipt
- the topic is derived by SADE; callers do not provide a topic string
- `status_url` remains authoritative even when notifications are enabled



Response examples

Accepted (HTTP 202):

```json
{
  "status": "ACCEPTED",
  "request_kind": "ENTRY_REQUEST",
  "message": "Entry request accepted for processing.",
  "evaluation_series_id": "8af4f8f3-5429-4d80-805d-2f6dc3f72159",
  "action_id": null,
  "status_url": "/entry-requests/8af4f8f3-5429-4d80-805d-2f6dc3f72159",
  "notifications": {
    "entry_request_updates": {
      "enabled": true,
      "transport": "MQTT",
      "topic": "notifications/entry/orgs/org-001/8af4f8f3-5429-4d80-805d-2f6dc3f72159",
      "retain": true,
      "qos": 1
    }
  }
}
```

Rejected (HTTP 409):

```json
{
  "status": "REJECTED",
  "request_kind": "ENTRY_REQUEST",
  "message": "Missing required registry records (pilot/uav/zone/model).",
  "failure_code": "MISSING_REGISTRY_RECORDS",
  "evaluation_series_id": null,
  "action_id": null,
  "status_url": null
}
```



### `GET /entry-requests/{evaluation_series_id}`

Reads the current workflow state for one logical entry request.  
Use the `status_url` from `POST /entry-request`.

This status resource is the operator-facing source of truth for the async entry workflow. In practice, that means:

1. scripts can poll it
2. a web UI can refresh or subscribe to it
3. long-running decision and attestation work does not need to block the original POST

If MQTT notifications were enabled on the request:

1. subscribe to the exact topic returned in the acceptance receipt
2. expect retained summary notifications for `APPROVED`, `APPROVED_CONSTRAINTS`, `ACTION_REQUIRED`, and `DENIED`
3. do not treat MQTT as authoritative; always use `status_url` for full workflow state

Status response example (HTTP 200)

```json
{
  "entry_request": {
    "evaluation_series_id": "8af4f8f3-5429-4d80-805d-2f6dc3f72159",
    "lifecycle_status": "COMPLETED",
    "decision": "ACTION_REQUIRED",
    "reason": "Stub forced action required decision.",
    "flight_session_id": null,
    "action_required": {
      "action_id": "f9ce1f1f-e7b7-40af-af6d-b6ba8cae0fe5",
      "lifecycle_status": "OPEN",
      "decision": null,
      "retries_used": 0,
      "max_retries": 1,
      "last_failure_code": null,
      "last_failure_reason": null,
      "evidence_requirement_spec": {
        "type": "EVIDENCE_REQUIREMENT",
        "spec_version": "1.0",
        "categories": []
      },
      "submitted_attestation_refs": []
    },
    "history": [
      {
        "evaluation_id": "0a3a...",
        "entry_request_kind": "ENTRY",
        "lifecycle_status": "COMPLETED",
        "decision": "ACTION_REQUIRED",
        "reason": "Stub forced action required decision."
      }
    ]
  }
}
```

Another rejected example:

```json
{
  "status": "REJECTED",
  "request_kind": "ENTRY_REQUEST",
  "message": "Requested window overlaps an existing pending or planned request for the same drone and pilot.",
  "failure_code": "OVERLAPPING_SCHEDULING_SUBJECT_WINDOW",
  "evaluation_series_id": null,
  "action_id": null,
  "status_url": null
}
```



## SafeCert API

When SADE requests evidence from SafeCert, it sends an `EVIDENCE_REQUIREMENT` payload that includes a `request_id`.

Important correlation rule:

1. SafeCert receives this correlation key as `request_id` in SADE's evidence request payload.
2. SafeCert must send that exact same value back in `in_response_to` when calling `/attestation-submission`.

### SADE -> SafeCert attestation request (outbound from SADE)

Transport is currently integration-dependent (`HTTP`, event-driven, or another channel to be finalized).  
At the moment, SADE does not have a live SafeCert HTTPS endpoint configured, so no real HTTP delivery occurs yet. SADE can create the outbound request and persist it internally, but SafeCert will not receive it over the network until that transport is wired.  
Payload contract shape:

Payload example (`type: EVIDENCE_REQUIREMENT`)

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
        { "expr": "PART_107", "keyword": "PART_107", "params": [] },
        { "expr": "BVLOS(FAA)", "keyword": "BVLOS", "params": ["FAA"] }
      ]
    },
    {
      "category": "CAPABILITY",
      "requirements": [
        { "expr": "NIGHT_FLIGHT", "keyword": "NIGHT_FLIGHT", "params": [] },
        {
          "expr": "PAYLOAD(weight<=2kg)",
          "keyword": "PAYLOAD",
          "params": [{ "key": "weight", "value": "<=2kg" }]
        }
      ]
    },
    {
      "category": "ENVIRONMENT",
      "requirements": [
        { "expr": "MAX_WIND_GUST(28mph)", "keyword": "MAX_WIND_GUST", "params": ["28mph"] }
      ]
    },
    {
      "category": "INTERFACE",
      "requirements": [
        { "expr": "SADE_ATC_API(v1)", "keyword": "SADE_ATC_API", "params": ["v1"] }
      ]
    }
  ]
}
```



### `POST /attestation-submission`

Submits evidence/attestation to satisfy an action-required decision.  
`in_response_to` must match the `request_id` from SADE's prior `EVIDENCE_REQUIREMENT` payload.
SafeCert sends this payload to SADE using the endpoint below.  
This endpoint returns a receipt, not the final workflow decision.

Request example

```json
{
  "idempotency_key": "dbafef25-44f2-449d-8bb6-85e4f9fc29f6",
  "submission_time_utc": "2026-03-09T20:02:00Z",
  "type": "EVIDENCE_ATTESTATION",
  "spec_version": "1.0",
  "attestation_id": "ATT-0001",
  "in_response_to": "REQ-0001",
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
          "expr": "PART_107",
          "keyword": "PART_107",
          "params": [],
          "meta": { "status": "SATISFIED", "cert_id": "107-ABCDE", "issuer": "FAA" }
        },
        {
          "expr": "BVLOS(FAA)",
          "keyword": "BVLOS",
          "params": ["FAA"],
          "meta": { "status": "SATISFIED", "waiver_id": "BVLOS-12345" }
        }
      ]
    },
    {
      "category": "CAPABILITY",
      "requirements": [
        {
          "expr": "NIGHT_FLIGHT",
          "keyword": "NIGHT_FLIGHT",
          "params": [],
          "meta": { "status": "SATISFIED", "actual": true }
        },
        {
          "expr": "PAYLOAD(weight<=2kg)",
          "keyword": "PAYLOAD",
          "params": [{ "key": "weight", "value": "<=2kg" }],
          "meta": { "status": "SATISFIED", "actual_max": "7kg" }
        }
      ]
    },
    {
      "category": "ENVIRONMENT",
      "requirements": [
        {
          "expr": "MAX_WIND_GUST(28mph)",
          "keyword": "MAX_WIND_GUST",
          "params": ["28mph"],
          "meta": { "status": "SATISFIED", "actual_limit": "30mph" }
        }
      ]
    },
    {
      "category": "INTERFACE",
      "requirements": [
        {
          "expr": "SADE_ATC_API(v1)",
          "keyword": "SADE_ATC_API",
          "params": ["v1"],
          "meta": { "status": "PARTIAL", "actual": "v1.0" }
        }
      ]
    }
  ],
  "signatures": [
    {
      "signer": "ORG-789",
      "signature_type": "DIGITAL_SIGNATURE",
      "signature_ref": "<opaque-reference>"
    }
  ],
  "evidence_refs": [
    {
      "evidence_id": "EVID-001",
      "kind": "DOCUMENT_OR_ARTIFACT",
      "ref": "<opaque-reference>"
    }
  ]
}
```

Required fields: `idempotency_key`, `submission_time_utc`, `type`, `spec_version`, `attestation_id`, `in_response_to`, `subject`, `categories`, `signatures`, `evidence_refs`.



Response examples

Accepted (HTTP 202):

```json
{
  "status": "ACCEPTED",
  "request_kind": "ATTESTATION_SUBMISSION",
  "message": "Attestation submission accepted for processing.",
  "evaluation_series_id": "8af4f8f3-5429-4d80-805d-2f6dc3f72159",
  "action_id": "f9ce1f1f-e7b7-40af-af6d-b6ba8cae0fe5",
  "status_url": "/actions/f9ce1f1f-e7b7-40af-af6d-b6ba8cae0fe5"
}
```

Rejected (HTTP 409):

```json
{
  "status": "REJECTED",
  "request_kind": "ATTESTATION_SUBMISSION",
  "message": "Unknown action_id.",
  "failure_code": "UNKNOWN_ACTION_ID",
  "evaluation_series_id": null,
  "action_id": "UNKNOWN-ACTION-ID",
  "status_url": null
}
```



### `GET /actions/{action_id}`

Reads the current action-required workflow state for one evidence request.  
Use the `status_url` from `POST /attestation-submission`.

Status response example (HTTP 200)

```json
{
  "action": {
    "action_id": "f9ce1f1f-e7b7-40af-af6d-b6ba8cae0fe5",
    "evaluation_series_id": "8af4f8f3-5429-4d80-805d-2f6dc3f72159",
    "lifecycle_status": "OPEN",
    "decision": null,
    "reason": "Missing required registry records (pilot/uav/zone/model).",
    "failure_code": "MISSING_REGISTRY_RECORDS",
    "flight_session_id": null,
    "action_required": {
      "action_id": "f9ce1f1f-e7b7-40af-af6d-b6ba8cae0fe5",
      "lifecycle_status": "OPEN",
      "decision": null,
      "retries_used": 0,
      "max_retries": 1,
      "last_failure_code": "MISSING_REGISTRY_RECORDS",
      "last_failure_reason": "Missing required registry records (pilot/uav/zone/model).",
      "evidence_requirement_spec": {
        "categories": []
      },
      "submitted_attestation_refs": []
    }
  }
}
```



### `POST /exit-request`

Operator exit-intent endpoint.  
Use this when the drone plans to leave early. This does not finalize the session. SADE queues the intent for Flight Monitor, and Flight Monitor decides the real end once the drone is offline.
Idempotency is keyed by `flight_session_id`.

Request example

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "request_time_utc": "2026-03-09T18:41:00Z",
  "reason": "Returning home early"
}
```

Request receipt examples

Accepted (HTTP 202):

```json
{
  "status": "ACCEPTED",
  "request_kind": "EXIT_REQUEST",
  "message": "Exit request accepted and queued for Flight Monitor.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834"
}
```

Rejected (HTTP 409):

```json
{
  "status": "REJECTED",
  "request_kind": "EXIT_REQUEST",
  "message": "Flight session not found: 8c189f91-0348-4a15-a6f0-23377dca7834",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "failure_code": "FLIGHT_SESSION_NOT_FOUND"
}
```


## Telemetry Monitor API

### `POST /tracker-session-finalized`

Tracker-authoritative closeout endpoint.  
Use this to finalize a planned session and persist final telemetry for reputation.
Idempotency is keyed by `flight_session_id`.

Request example

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "report_time_utc": "2026-03-09T19:05:00Z",
  "telemetry_summary": {
    "altitude_min_m": 12.0,
    "altitude_max_m": 94.5,
    "distance_flown_m": 1250.0
  },
  "events": [
    {
      "type": "FLIGHT_SEGMENT",
      "time_in_utc": "2026-03-09T18:00:00Z",
      "time_out_utc": "2026-03-09T19:03:00Z"
    }
  ]
}
```

SADE derives the actual flown window from the `events` list:

- earliest `FLIGHT_SEGMENT.time_in_utc`
- latest `FLIGHT_SEGMENT.time_out_utc`

For current Flight Monitor contract details and the event, incident-code, and payload-type conventions used in stored reputation records, see [SADE_CONTRACT.md](./FLIGHT_MONITOR/SADE_CONTRACT.md) and [REFERENCE_TABLES.md](./FLIGHT_MONITOR/REFERENCE_TABLES.md).



Scenario responses (HTTP 200)

Finalized:

```json
{
  "status": "EXITED",
  "reason": "Session finalized from tracker report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": "772d0ca7-0f5d-4b63-9f33-f5d6240be205"
}
```

Business failed:

```json
{
  "status": "FAILED",
  "reason": "No session found for tracker finalization report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": null
}
```


## Website Query APIs

These endpoints are intended for read-oriented website or operator UI views.

Common rules for both query endpoints:

- at least one filter is required: `organization_id`, `pilot_id`, or `drone_id`
- multiple filters use AND semantics
- optional `limit` defaults to `100`
- `limit` is capped at `200`

### `GET /reputation-records`

Primary Use: Website / operator UI

Lists stored reputation records already persisted by SADE.

Supported filters:

- `organization_id`
- `pilot_id`
- `drone_id`
- `limit`

Response rows are ordered by the latest recorded activity time descending.

Example request:

- `GET /reputation-records?organization_id=org-001&pilot_id=pilot-001`

Response example

```json
{
  "reputation_records": [
    {
      "reputation_record_id": "772d0ca7-0f5d-4b63-9f33-f5d6240be205",
      "evaluation_series_id": "series-001",
      "pilot_id": "pilot-001",
      "drone_id": "drone-001",
      "flight_session_id": "flight-session-001",
      "organization_id": "org-001",
      "sade_zone_id": "zone-001",
      "telemetry_summary": {
        "altitude_max_m": 88.0,
        "distance_flown_m": 1250.0
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
        "max_wind_knots": 18.0,
        "visibility_min_nm": 8.0,
        "window_start_utc": "2026-03-09T18:00:00Z",
        "window_end_utc": "2026-03-09T18:41:00Z"
      },
      "events": [
        {
          "type": "FLIGHT_SEGMENT",
          "time_in_utc": "2026-03-09T18:00:00Z",
          "time_out_utc": "2026-03-09T18:41:00Z",
          "battery_state_in": {
            "system_charge_pct": 98.0
          },
          "battery_state_out": {
            "system_charge_pct": 61.0
          }
        },
        {
          "type": "INCIDENT",
          "time_utc": "2026-03-09T18:41:00Z",
          "incident_code": "0101-100"
        }
      ],
      "created_at_utc": "2026-04-21T20:00:00Z"
    }
  ]
}
```

Validation error example (HTTP 400):

```json
{
  "error": {
    "reason": "At least one filter is required: organization_id, pilot_id, or drone_id."
  }
}
```


### `GET /attestation-claims`

Primary Use: Website / operator UI

Lists stored attestation claims from real attestation workflow submissions and from internal testing/scenario seeding.

Supported filters:

- `organization_id`
- `pilot_id`
- `drone_id`
- `limit`

Filter semantics:

- `organization_id` matches the stored attestation submission subject
- `pilot_id` matches claim bindings with subject type `PILOT`
- `drone_id` matches claim bindings with subject type `UAV`

Response rows are ordered by claim issuance time descending when available, otherwise by submission receive time descending.

Example request:

- `GET /attestation-claims?organization_id=org-001&pilot_id=pilot-001`

Response example

```json
{
  "attestation_claims": [
    {
      "claim_id": "claim-001",
      "submission_id": "submission-001",
      "attestation_id": "ATT-0001",
      "action_id": null,
      "organization_id": "org-001",
      "pilot_id": "pilot-001",
      "drone_id": "drone-001",
      "sade_zone_id": "zone-001",
      "source": "TESTING",
      "spec_type": "TESTING_ATTESTATION",
      "spec_version": "1.0",
      "received_at_utc": "2026-03-09T18:00:00Z",
      "requirement_id": "req-part-107",
      "category": "CERTIFICATION",
      "expr": "PART_107",
      "keyword": "PART_107",
      "status": "SATISFIED",
      "params": [],
      "meta": {
        "issuer": "TEST"
      },
      "issued_at_utc": null,
      "expires_at_utc": null,
      "evidence_ref": null,
      "signature_ref": null,
      "applicable_scopes": [
        "PILOT"
      ]
    }
  ]
}
```

## Testing / Scenario Seeding APIs

These endpoints are internal helpers for local, Docker, and AWS test scenarios.

They are useful when the Decision Maker team or UI team wants richer seeded data without having to drive the full upstream workflow first.

### `POST /testing/reputation-records`

Primary Use: Testing / scenario seeding

Creates a synthetic reputation record directly in SADE storage.

Required fields:

- `pilot_id`
- `drone_id`
- `sade_zone_id`
- `events`

Optional fields:

- `organization_id`
- `flight_session_id`
- `evaluation_series_id`
- `telemetry_summary`
- `declared_payload`
- `weather_observed`

Request example

```json
{
  "organization_id": "org-001",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "sade_zone_id": "zone-001",
  "telemetry_summary": {
    "altitude_max_m": 88.0,
    "distance_flown_m": 1250.0
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
    "max_wind_knots": 18.0,
    "visibility_min_nm": 8.0,
    "window_start_utc": "2026-03-09T18:00:00Z",
    "window_end_utc": "2026-03-09T18:41:00Z"
  },
  "events": [
    {
      "type": "FLIGHT_SEGMENT",
      "time_in_utc": "2026-03-09T18:00:00Z",
      "time_out_utc": "2026-03-09T18:41:00Z",
      "battery_state_in": {
        "system_charge_pct": 98.0
      },
      "battery_state_out": {
        "system_charge_pct": 61.0
      }
    },
    {
      "type": "INCIDENT",
      "time_utc": "2026-03-09T18:41:00Z",
      "incident_code": "0101-100"
    }
  ]
}
```

Event, incident-code, and payload-type conventions for seeded reputation records follow [REFERENCE_TABLES.md](./FLIGHT_MONITOR/REFERENCE_TABLES.md).

Response example

```json
{
  "status": "CREATED",
  "reputation_record": {
    "reputation_record_id": "772d0ca7-0f5d-4b63-9f33-f5d6240be205",
    "evaluation_series_id": null,
    "pilot_id": "pilot-001",
    "drone_id": "drone-001",
    "flight_session_id": null,
    "organization_id": "org-001",
    "sade_zone_id": "zone-001",
    "telemetry_summary": {
      "altitude_max_m": 88.0,
      "distance_flown_m": 1250.0
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
      "max_wind_knots": 18.0,
      "visibility_min_nm": 8.0,
      "window_start_utc": "2026-03-09T18:00:00Z",
      "window_end_utc": "2026-03-09T18:41:00Z"
    },
    "events": [
      {
        "type": "FLIGHT_SEGMENT",
        "time_in_utc": "2026-03-09T18:00:00Z",
        "time_out_utc": "2026-03-09T18:41:00Z",
        "battery_state_in": {
          "system_charge_pct": 98.0
        },
        "battery_state_out": {
          "system_charge_pct": 61.0
        }
      },
      {
        "type": "INCIDENT",
        "time_utc": "2026-03-09T18:41:00Z",
        "incident_code": "0101-100"
      }
    ],
    "created_at_utc": "2026-04-21T20:00:00Z"
  }
}
```


### `POST /testing/attestation-claims`

Primary Use: Testing / scenario seeding

Creates a synthetic attestation submission plus one or more normalized claims without requiring a real `action_id`.

Important behavior:

- at least one of `organization_id`, `pilot_id`, or `drone_id` is required
- synthetic submissions created here intentionally store `action_id = null`
- each claim may declare `applicable_scopes`
- supported `applicable_scopes` values are `PILOT` and `UAV`
- if a claim includes `PILOT`, the request must include `pilot_id`
- if a claim includes `UAV`, the request must include `drone_id`

Request example

```json
{
  "organization_id": "org-001",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "sade_zone_id": "zone-001",
  "received_at_utc": "2026-03-09T18:00:00Z",
  "attestation_id": "test-fake-claim",
  "claims": [
    {
      "requirement_id": "req-part-107",
      "category": "CERTIFICATION",
      "expr": "PART_107",
      "keyword": "PART_107",
      "status": "SATISFIED",
      "params": [],
      "meta": {
        "issuer": "TEST"
      },
      "applicable_scopes": [
        "PILOT"
      ]
    }
  ]
}
```

Response example

```json
{
  "status": "CREATED",
  "submission_id": "submission-001",
  "attestation_id": "test-fake-claim",
  "organization_id": "org-001",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "sade_zone_id": "zone-001",
  "source": "TESTING",
  "spec_type": "TESTING_ATTESTATION",
  "spec_version": "1.0",
  "received_at_utc": "2026-03-09T18:00:00Z",
  "attestation_claims": [
    {
      "claim_id": "claim-001",
      "submission_id": "submission-001",
      "attestation_id": "test-fake-claim",
      "action_id": null,
      "organization_id": "org-001",
      "pilot_id": "pilot-001",
      "drone_id": "drone-001",
      "sade_zone_id": "zone-001",
      "source": "TESTING",
      "spec_type": "TESTING_ATTESTATION",
      "spec_version": "1.0",
      "received_at_utc": "2026-03-09T18:00:00Z",
      "requirement_id": "req-part-107",
      "category": "CERTIFICATION",
      "expr": "PART_107",
      "keyword": "PART_107",
      "status": "SATISFIED",
      "params": [],
      "meta": {
        "issuer": "TEST"
      },
      "issued_at_utc": null,
      "expires_at_utc": null,
      "evidence_ref": null,
      "signature_ref": null,
      "applicable_scopes": [
        "PILOT"
      ]
    }
  ]
}
```
