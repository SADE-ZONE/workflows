# SADE / Flight Monitor Contract

**Last Updated On:** 2026-04-22

Unless noted otherwise, quantities, timestamps, and coordinate conventions follow [../QUANTITIES_AND_UNITS.md](../QUANTITIES_AND_UNITS.md).
Event, incident-code, and payload-type conventions live in [REFERENCE_TABLES.md](./REFERENCE_TABLES.md).

### Integration summary

- SADE sends one registration command at a time to `POST /flight-monitor/register-session`.
- SADE may also send an exit-intent command to `POST /flight-monitor/exit-request`.
- The Flight Monitor should immediately acknowledge acceptance with `202 Accepted`.
- The Flight Monitor later returns one finalization report to SADE by calling `POST /tracker-session-finalized`.
- `flight_session_id` is the primary correlation and idempotency key for both sides of this integration.

### Endpoint shape

- SADE -> Flight Monitor: `POST /flight-monitor/register-session`
- SADE -> Flight Monitor: `POST /flight-monitor/exit-request`
- Flight Monitor -> SADE: `POST /tracker-session-finalized`

### Current v1 rules

- outbound registration and exit-intent delivery are asynchronous from SADE through the outbox
- finalization callback into SADE is synchronous HTTP
- `flight_session_id` is the only required cross-system correlation key

## Register Session

When an entry request is approved and SADE creates a planned flight session, SADE sends a registration message to the Flight Monitor at `POST /flight-monitor/register-session`.

That message tells the Flight Monitor which approved session to track. Once the Flight Monitor receives it, it is allowed to begin recording telemetry for that session.

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "organization_id": "org-001",
  "sade_zone_id": "zone-001",
  "requested_entry_time_utc": "2026-03-09T18:00:00Z",
  "requested_exit_time_utc": "2026-03-09T19:00:00Z",
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  },
  "test_overrides": null,
  "submitted_at_utc": "2026-03-09T17:55:00Z"
}
```

Important notes:

- `requested_entry_time_utc` and `requested_exit_time_utc` are the planned authorized window, not the observed flown window.
- `requested_operation` is operational context for the Flight Monitor. SADE should treat it as an opaque object.
- `test_overrides` is only for local/dev testing with stubbed services. It is not part of the long-term production contract.

### Example with dev-only override

If the entry request includes `test_overrides.flight_monitor`, SADE forwards that object to the Flight Monitor as `test_overrides`.

This means the caller wants stub or simulated Flight Monitor behavior instead of waiting for real telemetry. That is useful for scenarios with fake drones or other test setups where real telemetry will never arrive and the session should be closed out automatically.

Example:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "organization_id": "org-001",
  "sade_zone_id": "zone-001",
  "requested_entry_time_utc": "2026-03-09T18:00:00Z",
  "requested_exit_time_utc": "2026-03-09T19:00:00Z",
  "requested_operation": {
    "operation_type": "INSPECTION",
    "priority": "NORMAL"
  },
  "test_overrides": {
    "telemetry_summary": {
      "altitude_max_m": 88.0,
      "distance_flown_m": 1250.0
    },
    "events": [
      {
        "type": "FLIGHT_SEGMENT",
        "time_in_utc": "2026-03-09T18:05:00Z",
        "time_out_utc": "2026-03-09T18:41:00Z"
      }
    ]
  },
  "submitted_at_utc": "2026-03-09T17:55:00Z"
}
```

This keeps the Flight Monitor rule simple:

- `test_overrides == null` means use the normal monitor path
- `test_overrides` object means use the stub or simulated path described by that object

## Exit Request

When an operator wants to leave early, SADE sends an exit-intent message to the Flight Monitor at `POST /flight-monitor/exit-request`.

This does not finalize the session. It only records intent to leave early. The Flight Monitor remains authoritative for the real end of flight and should finalize later, once the drone is judged offline.

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "request_time_utc": "2026-03-09T18:41:00Z",
  "reason": "Returning home early"
}
```

Important notes:

- this is an intent message, not a closeout message
- it does not reduce or rewrite the original approved window inside SADE
- once the Flight Monitor later finalizes the session, the drone can no longer operate under that session even if approved time remained
- the finalized reputation history should include an `EXIT_REQUEST` event in `events`

### Finalization callback response examples

These responses are returned by SADE when the Flight Monitor calls `POST /tracker-session-finalized`.

They are not the response to the earlier registration request. They are the response to the final closeout callback after the flight has actually ended.

Accepted outcome means SADE accepted the finalization callback, finalized the session, and persisted the reputation record.

```json
{
  "status": "EXITED",
  "reason": "Session finalized from tracker report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": "772d0ca7-0f5d-4b63-9f33-f5d6240be205"
}
```

Failure means SADE rejected the finalization callback for a business reason, such as:

- no matching session exists
- the reported time window is invalid
- the session is not in a finalizable state

```json
{
  "status": "FAILED",
  "reason": "No session found for tracker finalization report.",
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "reputation_record_id": null
}
```

## Tracker Session Finalized

### What the telemetry monitor should send to SADE

The telemetry monitor should send this payload to `POST /tracker-session-finalized`.

This payload should include the flight-authored data only.  
It should not include `declared_payload` or `weather_observed`, because those come from elsewhere in SADE.

Example callback payload:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "report_time_utc": "2026-03-09T19:05:00Z",
  "telemetry_summary": {
    "altitude_min_m": 12.0,
    "altitude_max_m": 88.0,
    "distance_flown_m": 1250.0
  },
  "events": [
    {
      "type": "FLIGHT_SEGMENT",
      "time_in_utc": "2026-03-09T18:05:00Z",
      "time_out_utc": "2026-03-09T18:41:00Z",
      "battery_state_in": {
        "system_charge_pct": 98.0,
        "slots": [
          {
            "slot_id": "A",
            "voltage_v": 24.8
          },
          {
            "slot_id": "B",
            "voltage_v": 24.6
          }
        ]
      },
      "battery_state_out": {
        "system_charge_pct": 61.0,
        "slots": [
          {
            "slot_id": "A",
            "voltage_v": 23.9
          },
          {
            "slot_id": "B",
            "voltage_v": 24.0
          }
        ]
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

SADE derives the actual flown window from the `events` list:

- earliest `FLIGHT_SEGMENT.time_in_utc`
- latest `FLIGHT_SEGMENT.time_out_utc`

### What SADE stores as the reputation record

SADE then stores a richer reputation record.

Some fields come directly from the telemetry monitor callback:

- `flight_session_id`
- `telemetry_summary`
- `events`

Some fields are derived or copied by SADE:

- `declared_payload` is copied from the original entry request
- `weather_observed` is looked up by SADE for the actual flown window
- `pilot_id`, `drone_id`, `organization_id`, and `sade_zone_id` come from the approved session and registry context

Example stored reputation shape:

```json
{
  "flight_session_id": "8c189f91-0348-4a15-a6f0-23377dca7834",
  "pilot_id": "pilot-001",
  "drone_id": "drone-001",
  "organization_id": "org-001",
  "sade_zone_id": "zone-001",
  "telemetry_summary": {
    "altitude_min_m": 12.0,
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
    "window_start_utc": "2026-03-09T18:05:00Z",
    "window_end_utc": "2026-03-09T18:41:00Z",
    "max_wind_knots": 18.0,
    "max_gust_knots": 24.0,
    "visibility_min_nm": 8.0
  },
  "events": [
    {
      "type": "FLIGHT_SEGMENT",
      "time_in_utc": "2026-03-09T18:05:00Z",
      "time_out_utc": "2026-03-09T18:41:00Z",
      "battery_state_in": {
        "system_charge_pct": 98.0,
        "slots": [
          {
            "slot_id": "A",
            "voltage_v": 24.8
          },
          {
            "slot_id": "B",
            "voltage_v": 24.6
          }
        ]
      },
      "battery_state_out": {
        "system_charge_pct": 61.0,
        "slots": [
          {
            "slot_id": "A",
            "voltage_v": 23.9
          },
          {
            "slot_id": "B",
            "voltage_v": 24.0
          }
        ]
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
