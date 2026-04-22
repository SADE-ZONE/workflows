# Postgres Table Schemas (SADE Prototype)

**Last Updated On:** 2026-04-22

This document explains each table in the current migration:
`/Users/tonyalarcon/repos/sade/sade-prototype/sade_core/repositories/sql/postgres/001_init.sql`.

If this document and SQL differ, the SQL migration is authoritative.

Canonical quantity units and timestamp or coordinate conventions follow [QUANTITIES_AND_UNITS.md](/Users/tonyalarcon/repos/sade/sade-prototype/documentation/client/QUANTITIES_AND_UNITS.md). This schema document focuses on current storage shape, which may still contain legacy names pending cleanup.

## `uav_models`

This table stores UAV model capabilities used by evaluation logic.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `model_id` | `TEXT` | Yes | Primary key. |
| `name` | `TEXT` | Yes | Human-readable model name. |
| `max_wind_tolerance_knots` | `DOUBLE PRECISION` | No | Max wind tolerance in knots. |
| `max_payload_cap_kg` | `DOUBLE PRECISION` | No | Optional max payload capacity in kilograms. |
| `max_temp_f` | `DOUBLE PRECISION` | No | Max supported temperature in Fahrenheit. |
| `min_temp_f` | `DOUBLE PRECISION` | No | Min supported temperature in Fahrenheit. |

## `uavs`

This table stores individual aircraft and links each to a model.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `drone_id` | `TEXT` | Yes | Primary key. |
| `model_id` | `TEXT` | Yes | Foreign key to `uav_models(model_id)`. |
| `organization_id` | `TEXT` | Yes | Organization that owns or controls this UAV record. |

Indexes:
- `idx_uavs_organization` on `(organization_id, drone_id)`.

## `pilots`

This table stores pilot identities and optional organization affiliation.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `pilot_id` | `TEXT` | Yes | Primary key. |
| `organization_id` | `TEXT` | No | Optional org association. |

Indexes:
- `idx_pilots_organization` on `(organization_id, pilot_id)`.

## `zones`

This table stores SADE zones and geometry/altitude constraints.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `sade_zone_id` | `TEXT` | Yes | Primary key. |
| `name` | `TEXT` | Yes | Zone name. |
| `polygon_geojson` | `JSONB` | Yes | Zone polygon GeoJSON payload. |
| `altitude_ceiling_m` | `DOUBLE PRECISION` | Yes | Max altitude in meters. |

## `entry_request_evaluations`

This table is the authoritative history of entry and retry evaluations, including decision input/output snapshots.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `evaluation_id` | `TEXT` | Yes | Primary key. |
| `evaluation_series_id` | `TEXT` | Yes | Groups an entry request with its retry evaluations. |
| `entry_request_kind` | `TEXT` | Yes | `ENTRY` or `RETRY`. |
| `pilot_id` | `TEXT` | Yes | Subject pilot. |
| `drone_id` | `TEXT` | Yes | Subject UAV. |
| `sade_zone_id` | `TEXT` | Yes | Subject zone. |
| `requested_entry_time_utc` | `TIMESTAMPTZ` | Yes | Requested entry time window start. |
| `requested_exit_time_utc` | `TIMESTAMPTZ` | Yes | Requested exit time window end. |
| `request_time_utc` | `TIMESTAMPTZ` | Yes | Time request was made. |
| `organization_id` | `TEXT` | No | Organization copied from the authoritative pilot record when available. |
| `requested_operation_json` | `JSONB` | Yes | Requested operation payload, default `{}`. |
| `declared_payload_json` | `JSONB` | Yes | Declared payload context from the entry request, default `{}`. |
| `test_overrides_json` | `JSONB` | Yes | Stored test-only override payload, default `{}`. |
| `notification_preferences_json` | `JSONB` | Yes | Stored notification opt-ins such as `entry_request_updates`, default `{}`. |
| `lifecycle_status` | `TEXT` | Yes | Evaluation lifecycle state (`RECEIVED`, `DECISION_PENDING`, `COMPLETED`, `FAILED`). |
| `decision_kind` | `TEXT` | No | Decision outcome (`APPROVED`, `APPROVED_CONSTRAINTS`, `DENIED`, `ACTION_REQUIRED`). |
| `decision_reason` | `TEXT` | Yes | Human/system reason. |
| `decision_output_snapshot` | `JSONB` | Yes | Stored decision-result snapshot, default `{}`. For async Decision Maker this is the raw callback/result snapshot SADE persisted for the evaluation. |
| `decision_input_snapshot` | `JSONB` | Yes | Stored internal decision-context snapshot, default `{}`. This is SADE's richer internal context, not necessarily identical to the exact outbound HTTP request. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Record creation time. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Last update time. |

Indexes:
- `idx_entry_request_evaluation_series` on `(evaluation_series_id, created_at_utc, request_time_utc)`.

Schema evolution notes:
- `organization_id`, `requested_operation_json`, `declared_payload_json`, `test_overrides_json`, and `notification_preferences_json` are added defensively with `ADD COLUMN IF NOT EXISTS`.
- the lifecycle-status check constraint is recreated defensively to include `DECISION_PENDING`.

## `action_required`

This table stores open/closed evidence-request actions produced by entry evaluation when attestation is required.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `action_id` | `TEXT` | Yes | Primary key. |
| `evaluation_id` | `TEXT` | Yes | Foreign key to `entry_request_evaluations(evaluation_id)`. |
| `evaluation_series_id` | `TEXT` | Yes | Logical request series id. |
| `lifecycle_status` | `TEXT` | Yes | Action lifecycle state (`OPEN`, `PROCESSING`, `CLOSED`). |
| `decision_kind` | `TEXT` | No | Final decision for closed actions (`APPROVED`, `APPROVED_CONSTRAINTS`, `DENIED`, `ACTION_REQUIRED`). `NULL` while open/processing. |
| `evidence_requirement_spec` | `JSONB` | Yes | Requirement envelope from decision output, default `{}`. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Creation time. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Last update time. |
| `max_retries` | `INTEGER` | Yes | Retry budget, default `1`. |
| `retries_used` | `INTEGER` | Yes | Retry count used, default `0`. |
| `submitted_attestation_refs` | `JSONB` | Yes | Tracked submitted claim refs, default `[]`. |
| `expires_at_utc` | `TIMESTAMPTZ` | No | Optional expiry. |
| `pilot_id` | `TEXT` | Yes | Subject pilot. |
| `drone_id` | `TEXT` | Yes | Subject UAV. |
| `sade_zone_id` | `TEXT` | Yes | Subject zone. |
| `organization_id` | `TEXT` | No | Optional subject org. |
| `requested_entry_time_utc` | `TIMESTAMPTZ` | Yes | Requested window start. |
| `requested_exit_time_utc` | `TIMESTAMPTZ` | Yes | Requested window end. |
| `last_failure_code` | `TEXT` | No | Last processing failure code recorded while an action was being worked, for example external decision-processing failure. |
| `last_failure_reason` | `TEXT` | No | Human/system reason paired with `last_failure_code`. |

Indexes:
- `idx_action_required_series` on `(evaluation_series_id)`.
- `idx_action_required_lifecycle_status` on `(lifecycle_status)`.

Constraints:
- lifecycle must be one of `OPEN`, `PROCESSING`, or `CLOSED`
- decision kind must be `NULL` for open/processing actions
- decision kind must be non-`NULL` for closed actions

## `flight_sessions`

This table tracks planned/exited flight sessions after approvals.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `session_id` | `TEXT` | Yes | Primary key. |
| `evaluation_id` | `TEXT` | Yes | Foreign key to `entry_request_evaluations(evaluation_id)`. |
| `evaluation_series_id` | `TEXT` | Yes | Logical request series id. |
| `pilot_id` | `TEXT` | Yes | Subject pilot. |
| `drone_id` | `TEXT` | Yes | Subject UAV. |
| `sade_zone_id` | `TEXT` | Yes | Subject zone. |
| `status` | `TEXT` | Yes | Session state (`PLANNED`, `EXITED`). |
| `time_in_utc` | `TIMESTAMPTZ` | Yes | Planned entry time at creation; later overwritten with actual start on finalization. |
| `time_out_utc` | `TIMESTAMPTZ` | No | Planned exit time at creation; later overwritten with actual end on finalization. |
| `telemetry_tracking_enabled` | `BOOLEAN` | Yes | Tracking flag. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Creation time. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Last update time. |

Indexes:
- `idx_flight_sessions_active_lookup` on `(drone_id, sade_zone_id, status)`.

## `reputation_records`

This table stores observed telemetry/environmental outcomes used for later entry decisions.

Storage still includes `sade_zone_id` because the original observed zone remains useful as provenance/context.
However, the current outward Decision Maker contract treats zone as context, not as reusable matching scope.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `reputation_record_id` | `TEXT` | Yes | Primary key. |
| `evaluation_series_id` | `TEXT` | No | Optional linked series. |
| `pilot_id` | `TEXT` | Yes | Subject pilot. |
| `drone_id` | `TEXT` | Yes | Subject UAV. |
| `flight_session_id` | `TEXT` | No | Optional linked flight session. |
| `organization_id` | `TEXT` | No | Optional org context. |
| `sade_zone_id` | `TEXT` | Yes | Subject zone. |
| `observed_at_utc` | `TIMESTAMPTZ` | Yes | Derived latest activity timestamp used for ordering/filtering. |
| `telemetry_summary_json` | `JSONB` | Yes | Summary telemetry payload, default `{}`. |
| `declared_payload_json` | `JSONB` | Yes | Declared payload context, default `{}`. |
| `weather_observed_json` | `JSONB` | Yes | Observed weather/environment payload, default `{}`. |
| `events_json` | `JSONB` | Yes | Event list payload, default `[]`. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Record creation time. |

Indexes:
- `idx_reputation_subject` on `(pilot_id, drone_id, sade_zone_id, observed_at_utc DESC)`.
- `idx_reputation_series` on `(evaluation_series_id)`.
- `idx_reputation_flight_session` on `(flight_session_id)`.
- `idx_reputation_organization_observed` on `(organization_id, observed_at_utc DESC)`.
- `idx_reputation_pilot_observed` on `(pilot_id, observed_at_utc DESC)`.
- `idx_reputation_drone_observed` on `(drone_id, observed_at_utc DESC)`.

Schema evolution notes:
- `flight_session_id`, `organization_id`, `telemetry_summary_json`, `declared_payload_json`, `weather_observed_json`, and `events_json` are added defensively with `ADD COLUMN IF NOT EXISTS`.
- legacy `telemetry_json`, `environmental_conditions_json`, `subject_context_json`, and `source` are explicitly dropped.

## `attestation_submissions`

This is the parent table for attestation ingestion. It preserves submission envelope/provenance and raw payload before/alongside claim normalization.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `submission_id` | `TEXT` | Yes | Primary key. |
| `action_id` | `TEXT` | No | Optional foreign key to `action_required(action_id)`. Real attestation workflow rows set this; testing/scenario-seeding rows may leave it null. |
| `evidence_request_id` | `TEXT` | No | Request/action correlation id from payload (`in_response_to`). |
| `attestation_id` | `TEXT` | No | Attestation document id. |
| `spec_type` | `TEXT` | Yes | Attestation type (for example `EVIDENCE_ATTESTATION`). |
| `spec_version` | `TEXT` | No | Contract version. |
| `pilot_id` | `TEXT` | No | Subject pilot from payload/fallback. |
| `drone_id` | `TEXT` | No | Subject drone from payload/fallback. |
| `organization_id` | `TEXT` | No | Subject org. |
| `sade_zone_id` | `TEXT` | No | Subject zone from payload/fallback. |
| `source` | `TEXT` | Yes | Ingestion source (for example `SAFECERT` or `TESTING`). |
| `received_at_utc` | `TIMESTAMPTZ` | Yes | Receipt timestamp. |
| `raw_payload_json` | `JSONB` | Yes | Full attestation payload snapshot. |

Constraints and cleanup:
- Duplicate rows by `(action_id, attestation_id)` are cleaned before index creation.
- Unique index `idx_attestation_action_attestation_unique` enforces one attestation id per action (when `attestation_id` is not null).
- `idx_attestation_submissions_organization_received` supports org-filtered claim browsing on `(organization_id, received_at_utc DESC)`.

## `claims`

This table stores normalized requirement-level claims extracted from attestation categories.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `claim_id` | `TEXT` | Yes | Primary key. |
| `submission_id` | `TEXT` | Yes | Foreign key to `attestation_submissions(submission_id)`. |
| `requirement_id` | `TEXT` | No | Stable requirement identity copied from the stored `evidence_requirement_spec` when available. |
| `category` | `TEXT` | Yes | Requirement category. |
| `expr` | `TEXT` | Yes | Canonical expression string. |
| `keyword` | `TEXT` | Yes | Requirement keyword. |
| `status` | `TEXT` | No | Requirement status (`SATISFIED`, `PARTIAL`, etc.). |
| `params_json` | `JSONB` | Yes | Requirement params array/object payload. |
| `meta_json` | `JSONB` | Yes | Requirement metadata payload. |
| `issued_at_utc` | `TIMESTAMPTZ` | No | Optional issue/generated timestamp. |
| `expires_at_utc` | `TIMESTAMPTZ` | No | Optional expiration timestamp. |
| `evidence_ref` | `TEXT` | No | Opaque evidence reference. |
| `signature_ref` | `TEXT` | No | Opaque signature reference. |

Indexes:
- `idx_claim_status` on `(status)`.
- `idx_claim_expires` on `(expires_at_utc)`.

Schema evolution notes:
- `requirement_id` is added defensively with `ADD COLUMN IF NOT EXISTS`.

## `claim_bindings`

This table binds each claim to one or more subject dimensions.

The table is generic, but the current normalized evidence model only relies on reusable claim scopes for:

- `PILOT`
- `UAV`

`ZONE` and `ORG` are no longer part of the intended reusable evidence-scope model, even though the table itself is not constrained to those values.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `claim_id` | `TEXT` | Yes | Foreign key to `claims(claim_id)`. |
| `subject_type` | `TEXT` | Yes | Subject kind. Current normalized usage is `PILOT` or `UAV`. |
| `subject_id` | `TEXT` | Yes | Subject identifier value. |

Primary key:
- `(claim_id, subject_type, subject_id)`.

Indexes:
- `idx_claim_binding_subject` on `(subject_type, subject_id)`.

## `idempotency_keys`

This table stores idempotency state per handler and key, including replay payload and lifecycle status.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `handler_name` | `TEXT` | Yes | Logical operation name (entry, attestation, decision-result, tracker-finalized, etc.). |
| `idempotency_key` | `TEXT` | Yes | Client-provided idempotency token. |
| `request_hash` | `TEXT` | Yes | Hash of request content for conflict detection. |
| `status` | `TEXT` | Yes | Persisted row lifecycle. Current stored values are `IN_PROGRESS` and `COMPLETED`. |
| `response_payload` | `JSONB` | No | Cached response for replay. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Creation time. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Last update time. |
| `expires_at_utc` | `TIMESTAMPTZ` | Yes | TTL cutoff for cleanup. |

Primary key:
- `(handler_name, idempotency_key)`.

Indexes:
- `idx_idempotency_expires_at` on `(expires_at_utc)`.

Important note:
- repository return statuses such as `ACQUIRED`, `CACHED`, and `HASH_MISMATCH` are application-layer results, not additional persisted values in this column

## `callback_outbox`

This table is the durable outbox for callback events. Publishers enqueue rows and worker(s) dispatch them asynchronously.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `outbox_id` | `BIGSERIAL` | Yes | Primary key, monotonic queue identity. |
| `target` | `TEXT` | Yes | Event destination (`SAFECERT`, `OPERATOR`, `DECISION_MAKER`, `FLIGHT_MONITOR`, etc.). |
| `event_type` | `TEXT` | Yes | Callback type. |
| `payload_json` | `JSONB` | Yes | Event payload. |
| `delivery_metadata_json` | `JSONB` | Yes | Transport metadata such as target topic, retain flag, or transport type, default `{}`. |
| `source_published_at_utc` | `TIMESTAMPTZ` | Yes | Event source timestamp. |
| `status` | `TEXT` | Yes | Delivery state, default `PENDING`. |
| `attempts` | `INTEGER` | Yes | Delivery attempts count, default `0`. |
| `available_at_utc` | `TIMESTAMPTZ` | Yes | Next eligible attempt time, default `NOW()`. |
| `processing_started_at_utc` | `TIMESTAMPTZ` | No | Worker claim timestamp. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Row creation time, default `NOW()`. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Row update time, default `NOW()`. |
| `published_at_utc` | `TIMESTAMPTZ` | No | Successful publish time. |
| `last_error` | `TEXT` | No | Last delivery error text. |

Indexes:
- `idx_callback_outbox_available` on `(status, available_at_utc, outbox_id)`.
- `idx_callback_outbox_processing` on `(status, processing_started_at_utc, outbox_id)`.

Schema evolution notes:
- `delivery_metadata_json` is added defensively with `ADD COLUMN IF NOT EXISTS`.

## `workflow_jobs`

This table is the durable internal workflow queue.

It is not for external delivery.
It is for SADE's own background workflow progression after a request has already been accepted.

In other words:

- `workflow_jobs` is how `api_runtime` hands internal work to `workflow_worker`
- `callback_outbox` is how business services hand external delivery work to `outbox_worker`

That distinction is the source of a lot of the architecture.

Typical examples:

- `POST /entry-request` creates an `entry_request_evaluations` row, then enqueues an `ENTRY_REQUEST` job here
- `POST /attestation-submission` stores the submission, then enqueues an `ATTESTATION_SUBMISSION` job here
- `POST /decision-result` persists the callback, then enqueues an `APPLY_DECISION_RESULT` job here

The `workflow_worker` later claims rows from this table, runs the real business processing, and marks jobs completed, retried, or dead-lettered.

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `job_id` | `TEXT` | Yes | Primary key. |
| `job_kind` | `TEXT` | Yes | Internal workflow type (`ENTRY_REQUEST`, `ATTESTATION_SUBMISSION`, `APPLY_DECISION_RESULT`). |
| `resource_id` | `TEXT` | Yes | Primary resource identity for the job, such as `evaluation_id` or `submission_id`. |
| `payload_json` | `JSONB` | Yes | Internal job payload used by `workflow_worker`, default `{}`. |
| `status` | `TEXT` | Yes | Job lifecycle (`PENDING`, `PROCESSING`, `COMPLETED`, `DEAD_LETTERED`), default `PENDING`. |
| `attempts` | `INTEGER` | Yes | Processing attempts count, default `0`. |
| `available_at_utc` | `TIMESTAMPTZ` | Yes | Next eligible attempt time, default `NOW()`. |
| `processing_started_at_utc` | `TIMESTAMPTZ` | No | Worker claim timestamp. |
| `created_at_utc` | `TIMESTAMPTZ` | Yes | Row creation time, default `NOW()`. |
| `updated_at_utc` | `TIMESTAMPTZ` | Yes | Row update time, default `NOW()`. |
| `last_error` | `TEXT` | No | Last processing error text. |

Indexes:
- `idx_workflow_jobs_available` on `(status, available_at_utc, created_at_utc)`.
- `idx_workflow_jobs_processing` on `(status, processing_started_at_utc, created_at_utc)`.

Constraints:
- `job_kind` must be one of `ENTRY_REQUEST`, `ATTESTATION_SUBMISSION`, or `APPLY_DECISION_RESULT`
- `status` must be one of `PENDING`, `PROCESSING`, `COMPLETED`, or `DEAD_LETTERED`

Schema evolution notes:
- the `job_kind` check constraint is recreated defensively to keep the allowed set in sync

Why this table exists:

- the API request should return quickly after durable acceptance
- the real workflow logic can take longer
- retries and dead-letter behavior should be durable
- business processing should not disappear just because a process crashes after acceptance

So yes: this repository is effectively the internal task queue for SADE itself.
