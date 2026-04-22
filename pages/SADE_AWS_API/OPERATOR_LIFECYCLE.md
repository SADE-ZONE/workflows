# Operator Lifecycle Guide (AWS Runtime)

**Last Updated On:** 2026-04-22

This guide is the practical sequence for operator-facing testing and integration.

Base URL used below:

`http://sarec-sade-use2-api-alb-1413405053.us-east-2.elb.amazonaws.com`

## 1) Create registry records first

Before requesting entry, seed all required registry records:

1. `POST /registry/uav-model`
2. `POST /registry/uav`
3. `POST /registry/pilot`
4. `POST /registry/zone`

If any required registry record is missing, `/entry-request` will return `lifecycle_status: "FAILED"`.

## 2) Submit entry request

Call:

- `POST /entry-request`

Possible outcomes:

1. HTTP `202` with `status: "ACCEPTED"` and a `status_url`
2. HTTP `409` with `status: "REJECTED"` and a `failure_code`

After acceptance, read `GET /entry-requests/{evaluation_series_id}` using the `status_url`.
If the workflow becomes action-required, the status response will include `action_required.action_id`.

Optional MQTT notifications:

1. Include `notifications.entry_request_updates.enabled=true` on `POST /entry-request` to request operator notifications.
2. If accepted, the receipt will include `notifications.entry_request_updates.topic`.
3. Subscribe to that exact topic if you want the retained latest summary for this workflow.
4. MQTT notifications are convenience signals only; `GET /entry-requests/{evaluation_series_id}` remains the authoritative state source.
5. SADE does not publish an MQTT message for the initial `ACCEPTED` receipt state. Current publishable entry outcomes are:
   - `APPROVED`
   - `APPROVED_CONSTRAINTS`
   - `ACTION_REQUIRED`
   - `DENIED`

Why this is asynchronous by design:

1. Entry evaluation can take variable time even before SafeCert is involved.
2. The decision adapter may be backed by an LLM or other external reasoning engine, and those calls can be slow, bursty, or temporarily unavailable.
3. If the decision becomes `ACTION_REQUIRED`, the workflow pauses for attestation. That introduces a human-in-the-loop dependency because evidence may need to be gathered, reviewed, and submitted later rather than immediately.
4. Holding the original HTTP request open across those stages would make SADE vulnerable to request timeouts, load balancer timeouts, client disconnects, retry storms, and inconsistent user experience when downstream services respond slowly.
5. Returning a `status_url` instead lets SADE run the workflow asynchronously and event-driven internally while giving operators one stable place to check progress.
6. In a UI, this becomes a simple status page or dashboard refresh problem rather than a long-lived request problem.

## 3) Force decisions for testing

In top-level `test_overrides.decision_maker`, set `force_decision` to drive deterministic test behavior.

Supported values:

1. `APPROVED`
2. `APPROVED_CONSTRAINTS`
3. `DENIED`
4. `ACTION_REQUIRED`
5. `NONE` (simulates Decision Maker returning no usable result, returns failed business outcome)
6. `RAISE` (simulates Decision Maker processing failure, returns failed business outcome)

Example snippet:

```json
{
  "test_overrides": {
    "decision_maker": {
      "force_decision": "ACTION_REQUIRED"
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

SafeCert testing hook:

1. When `force_decision` is `ACTION_REQUIRED`, the temporary Decision Maker stub also accepts `test_overrides.decision_maker.evidence_requirement_spec.categories`.
2. If provided, those categories replace the stub's default evidence categories for that forced action-required response.
3. This is useful for the SafeCert team to test different requirement sets without changing SADE code.
4. Only the requirement categories are overridden by this hook today; SADE still controls correlation and workflow identifiers.

Environmental testing hook:

1. `test_overrides.weather_service.forecast` may be provided on the entry request.
2. In local/dev flows, the no-op environmental service will use that supplied forecast instead of its default hardcoded values.
3. This is useful for end-to-end testing that wants deterministic environmental context without changing SADE code.

Flight-monitor testing hook:

1. `test_overrides.flight_monitor` may be provided on the entry request.
2. On approval, SADE forwards that object as the outbound Flight Monitor `test_overrides` value.
3. If `test_overrides.flight_monitor` is absent, SADE forwards outbound `test_overrides=null`.
4. This is intentionally a pass-through hook for stub/dev integrations, so SADE does not interpret the object contents.

## 4) Action-required continuation is SafeCert-owned (manual for now)

This stage is from the SafeCert system perspective, not the pilot/operator UI perspective.

Normal production intent:

1. SADE emits an evidence requirement (`request_id`) to SafeCert.
2. SafeCert evaluates requirements and sends `POST /attestation-submission`.
3. SafeCert sets `in_response_to` to that same `request_id`.

Current environment status:

1. SafeCert does not yet have a live HTTPS endpoint configured in SADE.
2. To complete an action-required SADE transaction, you must send `/attestation-submission` manually.
3. For manual testing, get `action_required.action_id` from the entry status response and use that as `in_response_to`.
4. SADE can still write outbound SafeCert requests to its internal outbox, but no actual HTTP delivery will happen until the SafeCert transport endpoint is provided and wired.

Operational reason:

1. This continuation is intentionally detached from the original entry HTTP request.
2. Once human review or document collection is involved, the elapsed time is no longer predictable.
3. The operator should therefore treat the status URL as the source of truth for ongoing progress, not the original `POST /entry-request` response or MQTT summary.
4. SADE also rejects overlapping windows for the same drone or same pilot, even before decisioning finishes.

## 5) Session finalization is telemetry-owned (manual for now)

This stage is from the telemetry monitor/tracker perspective, not the pilot/operator UI perspective.

Normal production intent:

1. SADE registers the approved session with the Flight Monitor.
2. Telemetry monitor confirms actual flight completion.
3. Telemetry monitor sends `POST /tracker-session-finalized` with observed timestamps and summary.

Current environment status:

1. Telemetry monitor integration is not wired yet.
2. To complete a session in testing, call `/tracker-session-finalized` manually.
3. Use the same `flight_session_id` from the approved entry session.
4. Expected success result is `status: "EXITED"`.

Why this design exists:

1. Final closeout is based on telemetry-truth (actual observations), not only operator/operator-app intent.
2. The authoritative closeout event is the tracker callback, not a separate stop request.

## 6) Session discipline rule for operators

Operator process should treat one drone as one active session at a time.

Practical rule:

1. Do not run overlapping zone sessions for the same drone.
2. Finalize the active session (`EXITED`) before submitting the next zone entry for that drone.

This keeps state and audit history consistent, and avoids ambiguity in operational ownership of the active flight.
