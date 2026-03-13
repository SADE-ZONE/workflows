# SADE Client API Reference (AWS)

Status date: 2026-03-12

This is the client-facing API contract for teams integrating with the deployed SADE AWS runtime.

## Base URL

`http://sarec-sade-use2-api-alb-1413405053.us-east-2.elb.amazonaws.com`

## Common rules

1. `POST` endpoints require `Content-Type: application/json`.
2. Workflow `POST` endpoints require `idempotency_key`.
3. Async workflow `POST` endpoints return a receipt first, not the final business outcome.
4. `POST /entry-request` and `POST /attestation-submission` return `RequestReceipt` with HTTP `202` on acceptance.
5. `POST /exit-request` and `POST /tracker-session-finalized` remain synchronous and return their final result contracts.
6. Validation/transport errors use HTTP `400` or `500`.

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
4. `Zone`: the SADE-managed flight area (polygon + altitude ceiling).
5. `Upsert`: create the record if it does not exist, or update it if it already exists.

## Registry API

The registry is the required reference data layer.  
Create these records first, then use workflow routes like `/entry-request`.

### `POST /registry/uav-model`

Registers a UAV model in SADE.  
Uses upsert behavior by `model_id`.

<details>
<summary>Request and response example</summary>

Request:

```json
{
  "model_id": "model-001",
  "name": "DJI Mavic 3",
  "max_wind_tolerance": 22.5,
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
    "max_wind_tolerance": 22.5,
    "max_temp_f": 110.0,
    "min_temp_f": -10.0
  }
}
```

</details>

### `POST /registry/uav`

Registers a specific UAV (drone) and links it to its `model_id`.  
Uses upsert behavior by `drone_id`.

<details>
<summary>Request and response example</summary>

Request:

```json
{
  "drone_id": "drone-001",
  "model_id": "model-001",
  "owner_id": "owner-001"
}
```

Response:

```json
{
  "status": "UPSERTED",
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "owner_id": "owner-001"
  }
}
```

</details>

### `POST /registry/pilot`

Registers a pilot identity used in entry and attestation workflows.  
Uses upsert behavior by `pilot_id`.

<details>
<summary>Request and response example</summary>

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

</details>

### `POST /registry/zone`

Registers a SADE zone boundary and altitude policy.  
Uses upsert behavior by `sade_zone_id`.

<details>
<summary>Request and response example</summary>

Request:

```json
{
  "sade_zone_id": "zone-001",
  "name": "Zone 001",
  "polygon": {
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
    "polygon": {
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

</details>

### Registry GET endpoints

- `GET /registry/uav-model/{model_id}`
- `GET /registry/uav/{drone_id}`
- `GET /registry/pilot/{pilot_id}`
- `GET /registry/zone/{sade_zone_id}`

Fetches one registry record by id.  
Returns HTTP `404` if the record does not exist.

<details>
<summary>GET response examples</summary>

Example `GET /registry/uav/drone-001`:

```json
{
  "uav": {
    "drone_id": "drone-001",
    "model_id": "model-001",
    "owner_id": "owner-001"
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

</details>

## Operator APIs

### `GET /health`

Light service liveness check used by humans, scripts, and load balancer health checks.

<details>
<summary>Response example</summary>

```json
{
  "status": "ok",
  "mode": "prod"
}
```

</details>

### `POST /entry-request`

Requests authorization for a UAV + pilot to enter a specific zone for a time window.  
This is now an asynchronous command endpoint.  
It returns a receipt, not the final decision body.

This is intentional, not temporary. The endpoint acknowledges durable workflow acceptance first, then the caller follows the returned `status_url` for progress and outcome.

<details>
<summary>Request example</summary>

```json
{
  "idempotency_key": "a8d87030-f7ea-4301-b03a-9de4f843c5fe",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "sade_zone_id": "zone-001",
  "organization_id": "org-001",
  "requested_entry_time": "2026-03-09T18:00:00Z",
  "requested_exit_time": "2026-03-09T19:00:00Z",
  "request_time": "2026-03-09T17:55:00Z",
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  }
}
```

Optional test-only forcing hook (inside `requested_operation`):

- `force_decision`: `APPROVED`, `APPROVED_CONSTRAINTS`, `DENIED`, `ACTION_REQUIRED`, `NONE`, `RAISE`
- when `force_decision` is `ACTION_REQUIRED`, you may also provide `evidence_requirement_spec.categories` to override the stub's default requirement categories for SafeCert testing

Example override shape:

```json
{
  "requested_operation": {
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
  }
}
```

This is a testing hook for the stub decision adapter. It is useful when the SafeCert team wants to exercise different evidence requirement sets without changing SADE code.

</details>

<details>
<summary>Request receipt examples</summary>

Accepted (HTTP 202):

```json
{
  "status": "ACCEPTED",
  "request_kind": "ENTRY_REQUEST",
  "message": "Entry request accepted for processing.",
  "evaluation_series_id": "8af4f8f3-5429-4d80-805d-2f6dc3f72159",
  "action_id": null,
  "status_url": "/entry-requests/8af4f8f3-5429-4d80-805d-2f6dc3f72159"
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



</details>

### `GET /entry-requests/{evaluation_series_id}`

Reads the current workflow state for one logical entry request.  
Use the `status_url` from `POST /entry-request`.

This status resource is the operator-facing source of truth for the async entry workflow. In practice, that means:

1. scripts can poll it
2. a web UI can refresh or subscribe to it
3. long-running decision and attestation work does not need to block the original POST

<details>
<summary>Status response example (HTTP 200)</summary>

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

</details>

### `POST /exit-request`

Signals operator intent to end a session.  
This does not finalize a session by itself; tracker finalization is required.

<details>
<summary>Request example</summary>

```json
{
  "idempotency_key": "f3e1a531-bf7e-469f-bdb4-b67f44d4af66",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "drone_id": null,
  "sade_zone_id": null,
  "request_time": "2026-03-09T19:10:00Z"
}
```

`flight_session_id` can be omitted if `drone_id` + `sade_zone_id` are provided.

</details>

<details>
<summary>Scenario responses (HTTP 200)</summary>

Accepted intent (not final closeout):

```json
{
  "status": "REQUESTED",
  "reason": "Exit requested; awaiting tracker finalization.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834"
}
```

Business failed:

```json
{
  "status": "FAILED",
  "reason": "No active session found for exit request.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834"
}
```

</details>

## SafeCert API

When SADE requests evidence from SafeCert, it sends an `EVIDENCE_REQUIREMENT` payload that includes a `request_id`.

Important correlation rule:

1. SafeCert receives this correlation key as `request_id` in SADE's evidence request payload.
2. SafeCert must send that exact same value back in `in_response_to` when calling `/attestation-submission`.

### SADE -> SafeCert attestation request (outbound from SADE)

Transport is currently integration-dependent (`HTTP`, event-driven, or another channel to be finalized).  
At the moment, SADE does not have a live SafeCert HTTPS endpoint configured, so no real HTTP delivery occurs yet. SADE can create the outbound request and persist it internally, but SafeCert will not receive it over the network until that transport is wired.  
Payload contract shape:

<details>
<summary>Payload example (`type: EVIDENCE_REQUIREMENT`)</summary>

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

</details>

### `POST /attestation-submission`

Submits evidence/attestation to satisfy an action-required decision.  
`in_response_to` must match the `request_id` from SADE's prior `EVIDENCE_REQUIREMENT` payload.
SafeCert sends this payload to SADE using the endpoint below.  
This endpoint returns a receipt, not the final workflow decision.

<details>
<summary>Request example</summary>

```json
{
  "idempotency_key": "dbafef25-44f2-449d-8bb6-85e4f9fc29f6",
  "submission_time": "2026-03-09T20:02:00Z",
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

Required fields: `idempotency_key`, `submission_time`, `type`, `spec_version`, `attestation_id`, `in_response_to`, `subject`, `categories`, `signatures`, `evidence_refs`.

</details>

<details>
<summary>Request receipt examples</summary>

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



</details>

### `GET /actions/{action_id}`

Reads the current action-required workflow state for one evidence request.  
Use the `status_url` from `POST /attestation-submission`.

<details>
<summary>Status response example (HTTP 200)</summary>

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

</details>

## Telemetry Monitor API

### `POST /tracker-session-finalized`

Tracker-authoritative closeout endpoint.  
Use this to finalize an in-zone session and persist final telemetry for reputation.

<details>
<summary>Request example</summary>

```json
{
  "idempotency_key": "13a32797-c9ab-47aa-96d2-b9c11ef36e77",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "report_time": "2026-03-09T19:05:00Z",
  "actual_start_time": "2026-03-09T18:00:00Z",
  "actual_end_time": "2026-03-09T19:03:00Z",
  "telemetry_summary": {
    "altitude_min_m": 12.0,
    "altitude_max_m": 94.5,
    "battery_start_pct": 98.0,
    "battery_end_pct": 61.0,
    "battery_voltage_start_v": 16.2,
    "battery_voltage_end_v": 14.9
  }
}
```

</details>

<details>
<summary>Scenario responses (HTTP 200)</summary>

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

</details>



## Route list

- `GET /health`
- `POST /entry-request`
- `GET /entry-requests/{evaluation_series_id}`
- `POST /attestation-submission`
- `GET /actions/{action_id}`
- `POST /exit-request`
- `POST /tracker-session-finalized`
- `POST /registry/uav-model`
- `POST /registry/uav`
- `POST /registry/pilot`
- `POST /registry/zone`
- `GET /registry/uav-model/{model_id}`
- `GET /registry/uav/{drone_id}`
- `GET /registry/pilot/{pilot_id}`
- `GET /registry/zone/{sade_zone_id}`
