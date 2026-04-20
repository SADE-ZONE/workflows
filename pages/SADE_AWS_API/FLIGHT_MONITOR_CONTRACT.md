## 2. Flight Monitor

**Last Updated On:** 2026-04-20

### Integration summary

- SADE sends one registration command at a time to `POST /flight-monitor/register-session`.
- The Flight Monitor should immediately acknowledge acceptance with `202 Accepted`.
- The Flight Monitor later returns one finalization report to SADE by calling `POST /tracker-session-finalized`.
- `flight_session_id` is the primary correlation and idempotency key for both sides of this integration.

For v1, SADE sends only one outbound command type:

- register/start monitoring for one approved planned session

For v1, the Flight Monitor sends one final callback per `flight_session_id`:

- one final session report through `POST /tracker-session-finalized`

### Endpoint shape

- SADE -> Flight Monitor: `POST /flight-monitor/register-session`
- Flight Monitor -> SADE: `POST /tracker-session-finalized`

### Registration request contract

Suggested request example:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "organization_id": "org-001",
  "sade_zone_id": "zone-001",
  "requested_entry_time": "2026-03-09T18:00:00Z",
  "requested_exit_time": "2026-03-09T19:00:00Z",
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  },
  "test_overrides": null,
  "submitted_at": "2026-03-09T17:55:00Z"
}
```

Important notes:

- `requested_entry_time` and `requested_exit_time` are the planned authorized window, not the observed flown window.
- `requested_operation` is operational context for the Flight Monitor. SADE should treat it as an opaque object.
- `evaluation_series_id` is intentionally not included in this outward request. `flight_session_id` is the tracker-facing correlation key.
- `test_overrides` is only for local/dev testing with stubbed services. It is not part of the long-term production contract.

### Example with dev-only override

If the entry request includes `test_overrides.flight_monitor`, SADE flattens that object and forwards it as the outbound Flight Monitor `test_overrides` value.

Example:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "organization_id": "org-001",
  "sade_zone_id": "zone-001",
  "requested_entry_time": "2026-03-09T18:00:00Z",
  "requested_exit_time": "2026-03-09T19:00:00Z",
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  },
  "test_overrides": {
    "actual_start_time": "2026-03-09T18:05:00Z",
    "actual_end_time": "2026-03-09T18:41:00Z",
    "telemetry_summary": {
      "altitude_min_m": 12.0,
      "altitude_max_m": 88.0,
      "battery_start_pct": 98.0,
      "battery_end_pct": 61.0
    }
  },
  "submitted_at": "2026-03-09T17:55:00Z"
}
```

For the current stub/testing direction:

- if `test_overrides.flight_monitor` is absent on the original entry request, SADE forwards outbound `test_overrides=null`
- if `test_overrides.flight_monitor` is present and is an object, SADE forwards that object unchanged as outbound `test_overrides`

This keeps the Flight Monitor stub rule simple:

- `test_overrides == null` means normal stub behavior
- `test_overrides` object means apply the stub-specific override

### Field meanings

- `flight_session_id`: stable session identifier created by SADE when approval produces a planned session
- `pilot_id`: pilot assigned to the authorized session
- `drone_id`: UAV assigned to the authorized session
- `organization_id`: organization context for routing, multi-tenant separation, and downstream reporting
- `sade_zone_id`: authorized SADE zone identifier
- `requested_entry_time`: planned start of the authorized window
- `requested_exit_time`: planned end of the authorized window
- `requested_operation`: operation context provided by the original entry request
- `test_overrides`: nullable dev-only stub hook for the Flight Monitor service
- `submitted_at`: time SADE published the outbound command

### Finalization callback contract

Suggested callback request example:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "report_time": "2026-03-09T19:05:00Z",
  "actual_start_time": "2026-03-09T18:05:00Z",
  "actual_end_time": "2026-03-09T18:41:00Z",
  "telemetry_summary": {
    "altitude_min_m": 12.0,
    "altitude_max_m": 88.0,
    "battery_start_pct": 98.0,
    "battery_end_pct": 61.0,
    "battery_voltage_start_v": 16.2,
    "battery_voltage_end_v": 14.9
  }
}
```

This callback tells SADE what actually happened, not what was authorized.

That means:

- `actual_start_time` and `actual_end_time` replace the planned session window as the true observed flight window
- `telemetry_summary` is what SADE persists into the reputation/closeout path

### Finalization callback response examples

Accepted business outcome:

```json
{
  "status": "EXITED",
  "reason": "Session finalized from tracker report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": "772d0ca7-0f5d-4b63-9f33-f5d6240be205"
}
```

Business failure:

```json
{
  "status": "FAILED",
  "reason": "No session found for tracker finalization report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": null
}
```

### Current v1 rules

- outbound registration is asynchronous from SADE through the outbox
- finalization callback into SADE is synchronous HTTP
- `flight_session_id` is the only required cross-system correlation key
- SADE does not currently send a separate stop/deregister command
- the Flight Monitor is authoritative for actual start/end timing in the finalization callback
