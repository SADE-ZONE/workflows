# Core Domain Models

## `UAVModel`

Purpose: Defines the aircraft model capabilities/limits used during UAV registration and SADE entry evaluation (for example wind/temperature capability checks).


| Attribute            | Type     | Meaning                                                          |
| -------------------- | -------- | ---------------------------------------------------------------- |
| `name`               | `str`    | Model identifier/name (primary identity for model registration). |
| `wingspan`           | `float?` | Aircraft wingspan (optional).                                    |
| `max_airspeed`       | `float?` | Maximum airspeed capability (optional).                          |
| `max_wind_tolerance` | `float?` | Maximum wind tolerance/capability (optional).                    |
| `max_temp`           | `float?` | Maximum supported operating temperature (optional).              |
| `min_temp`           | `float?` | Minimum supported operating temperature (optional).              |


## `UAV`

Purpose: Represents a registered UAV (specific aircraft instance) that SADE can identify, validate, and associate with zones/sessions.


| Attribute         | Type  | Meaning                    |
| ----------------- | ----- | -------------------------- |
| `id`              | `str` | UAV/drone identifier.      |
| `model_name`      | `str` | Link to `UAVModel.name`.   |
| `organization_id` | `str` | Owner/operator identifier. |


## `Pilot`

Purpose: Represents a pilot/operator identity record that SADE can reference for entry decisions, certifications/attestations, reputation lookups, and organization affiliation.


| Attribute            | Type         | Meaning                                                                |
| -------------------- | ------------ | ---------------------------------------------------------------------- |
| `pilot_id`           | `str`        | Unique pilot identifier used across SADE/reputation/trust systems.     |
| `organization_id`    | `str?`       | Organization/company the pilot belongs to.                             |
| `certification_refs` | `list[str]?` | References to pilot certificates/attestations (or trust artifact IDs). |
| `status`             | `str?`       | Pilot status (e.g., `ACTIVE`, `SUSPENDED`, `REVIEW`).                  |
| `created_at`         | `str?`       | Record creation time.                                                  |
| `updated_at`         | `str?`       | Last update time.                                                      |


## `SADEZone`

Purpose: Represents a managed SADE operating zone and its geometric/altitude constraints, plus the current active UAVs in the zone for operational awareness (for example occupancy/density).


| Attribute          | Type         | Meaning                                                                                                                    |
| ------------------ | ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `zone_id`          | `str`        | Zone identifier.                                                                                                           |
| `name`             | `str?`       | Human-readable zone name.                                                                                                  |
| `polygon`          | `str`        | Polygon geometry as JSON string (current implementation).                                                                  |
| `altitude_ceiling` | `float`      | Zone altitude ceiling/limit.                                                                                               |
| `active_uav_ids`   | `list[str]?` | Current active UAVs in the zone (operational view for density/monitoring; can be derived from active sessions if desired). |


# Entry Decision and Action Workflow Models

## `Entry Decision Result`

Purpose: Captures the decision SADE returns for an entry request, including request context, decision inputs, and decision outputs.


| Focus                   | Attribute                  | Type                              | Meaning                                                                                                                        |
| ----------------------- | -------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `Metadata`              | `entry_decision_result_id` | `str`                             | Entry decision result identifier.                                                                                              |
| `Metadata`              | `timestamp`                | `str`                             | Decision timestamp.                                                                                                            |
| `Entry Request Context` | `sade_zone`                | `SADEZone`                        | The SADE zone object for the decision context.                                                                                 |
| `Entry Request Context` | `uav`                      | `UAV`                             | The UAV object for the decision context.                                                                                       |
| `Entry Request Context` | `pilot`                    | `Pilot`                           | The pilot object for the decision context.                                                                                     |
| `Decision Basis`        | `environmental_conditions` | `SessionEnvironmentalConditions?` | Environmental conditions object used for this decision.                                                                        |
| `Decision Basis`        | `reputation_model_ids`     | `list[str]?`                      | Reputation model identifiers used/evaluated for this decision.                                                                 |
| `Decision Basis`        | `aircraft_attestations`    | `list[AttestationRecord]?`        | Attestations on file for the aircraft that were considered during this decision (for example SafeCert-generated attestations). |
| `Decision Output`       | `decision`                 | `str`                             | One of: `APPROVED`, `APPROVED-CONSTRAINTS`, `ACTION-REQUIRED`, `DENIED`.                                                       |
| `Decision Output`       | `constraints`              | `list[str]?`                      | Constraints imposed when decision is `APPROVED-CONSTRAINTS` (for example speed/altitude limits).                               |
| `Decision Output`       | `action_required_record`   | `ActionRequiredRecord?`           | Optional follow-up record; present when decision is `ACTION-REQUIRED`.                                                         |


## `Action Required Record`

Purpose: Describes the actions/evidence needed for an entry request to move from `ACTION-REQUIRED` to an approvable state. This should stay focused on the required actions, not duplicate the full request context.


| Attribute                   | Type         | Meaning                                                                                                                                                                                           |
| --------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `action_id`                 | `str`        | Identifier for the action-required workflow instance.                                                                                                                                             |
| `status`                    | `str`        | Action lifecycle state (`OPEN`, `SUBMITTED`, `SATISFIED`, `EXPIRED`, etc.).                                                                                                                       |
| `evidence_requirement_spec` | `str?`       | Optional machine-readable evidence requirement specification ( see [evidence_request_payload.json](https://github.com/SADE-ZONE/workflows/blob/main/figures/json/evidence_request_payload.json)). |
| `submitted_artifact_refs`   | `list[str]?` | References to submitted certificates/attestations/evidence responses. (see [evidence_data_exchange.md](https://github.com/SADE-ZONE/workflows/blob/main/pages/evidence_data_exchange.md) )        |
| `created_at`                | `str?`       | Creation timestamp.                                                                                                                                                                               |
| `updated_at`                | `str?`       | Last updated timestamp.                                                                                                                                                                           |
| `expires_at`                | `str?`       | Optional deadline for satisfying the actions.                                                                                                                                                     |


## `AttestationRecord`

Purpose: Represents an attestation saved by SADE (for example from SafeCert) for a specific aircraft, including the integrity hash and the evidence attestation content used for future entry decisions.


| Attribute              | Type     | Meaning                                                                                                     |
| ---------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `attestation_id`       | `str`    | Attestation identifier.                                                                                     |
| `uav`                  | `UAV`    | Aircraft/UAV object this attestation applies to.                                                            |
| `generated_on`         | `str`    | When the attestation was generated.                                                                         |
| `expires_on`           | `str?`   | When the attestation expires (if applicable).                                                               |
| `hash`                 | `str`    | Integrity hash stored with the attestation (for example blockchain-linked hash).                            |
| `evidence_attestation` | `object` | The attestation payload/content (most important field), including the evidence/claims returned by SafeCert. |


## `SessionEnvironmentalConditions`

Purpose: Stores the environmental conditions considered for a session (one-to-one with `SADESession`) across a relevant time window, supporting both forecast-based decisioning and observed summaries.


| Attribute               | Type     | Meaning                                                                           |
| ----------------------- | -------- | --------------------------------------------------------------------------------- |
| `id`                    | `str`    | Environmental conditions record identifier.                                       |
| `session_id`            | `str`    | One-to-one reference to the related session.                                      |
| `phase`                 | `str`    | Environmental context phase (for example `PLANNED`, `DECISION_TIME`, `OBSERVED`). |
| `window_start`          | `str?`   | Start of environmental time window considered (ISO timestamp).                    |
| `window_end`            | `str?`   | End of environmental time window considered (ISO timestamp).                      |
| `temperature_min_f`     | `float?` | Min temperature within the considered window.                                     |
| `temperature_max_f`     | `float?` | Max temperature within the considered window.                                     |
| `wind_steady_min_mph`   | `float?` | Min sustained wind within the window.                                             |
| `wind_steady_max_mph`   | `float?` | Max sustained wind within the window.                                             |
| `wind_gust_min_mph`     | `float?` | Min gust within the window (optional).                                            |
| `wind_gust_max_mph`     | `float?` | Max gust within the window.                                                       |
| `precipitation_summary` | `str?`   | Precipitation summary/category for the window.                                    |
| `lighting`              | `str?`   | Lighting/day-night conditions relevant to the session window.                     |
| `visibility_min_nm`     | `float?` | Minimum visibility in the window (if considered).                                 |
| `conditions_summary`    | `str?`   | Human-readable summary of key environmental conditions.                           |
| `confidence`            | `float?` | Confidence score (especially useful when forecast-derived).                       |
| `source`                | `str?`   | Environmental data provider/service source.                                       |
| `source_ref`            | `str?`   | Provider request/version/reference for traceability.                              |
| `generated_at`          | `str?`   | When this environmental summary was generated.                                    |


# Session Closeout and Reputation Models

## `ReputationRecord`

Purpose: Represents SADE's canonical post-flight reputation record produced on/after exit, using finalized/observed environmental conditions and finalized telemetry for the completed session, and tracking submission state to an external reputation service.


| Attribute                  | Type                              | Meaning                                                                                 |
| -------------------------- | --------------------------------- | --------------------------------------------------------------------------------------- |
| `reputation_record_id`     | `str`                             | SADE reputation record identifier.                                                      |
| `sade_zone`                | `SADEZone`                        | SADE zone object for the completed session.                                             |
| `uav`                      | `UAV`                             | UAV object for the completed session.                                                   |
| `pilot`                    | `Pilot`                           | Pilot object for the completed session.                                                 |
| `session`                  | `SADESession`                     | Finalized session object associated with this reputation record.                        |
| `environmental_conditions` | `SessionEnvironmentalConditions?` | Finalized/observed environmental conditions used for closeout and reputation recording. |
| `telemetry`                | `DroneTelemetry?`                 | Finalized telemetry aggregate/summary for the completed session.                        |
| `entry_decision_result`    | `EntryDecisionResult?`            | Entry decision result associated with the session (useful for audit/context).           |
| `incidents`                | `list[str]?`                      | Incident codes/events relevant to reputation scoring.                                   |
| `updated_at`               | `str?`                            | Last update time.                                                                       |


## `DroneTelemetry`

Purpose: Captures the finalized telemetry aggregate for a completed session (primarily altitude and battery summaries) used during closeout and reputation recording.


| Attribute               | Type     | Meaning                                              |
| ----------------------- | -------- | ---------------------------------------------------- |
| `uav_id`                | `str`    | Actual UAV ID correlated to the telemetry stream.    |
| `first_seen`            | `float?` | First-seen telemetry timestamp.                      |
| `last_update`           | `float?` | Last telemetry timestamp included in the aggregate.  |
| `max_altitude_m`        | `float?` | Maximum altitude observed during the tracked period. |
| `min_altitude_m`        | `float?` | Minimum altitude observed during the tracked period. |
| `battery_level_start`   | `float?` | Battery level at the start of tracked telemetry.     |
| `battery_level_end`     | `float?` | Battery level at the end of tracked telemetry.       |
| `battery_voltage_start` | `float?` | Battery voltage at start of tracked telemetry.       |
| `battery_voltage_end`   | `float?` | Battery voltage at end of tracked telemetry.         |
| `start_position`        | `tuple?` | Initial `(lat, lon, alt)` position if available.     |


# Misc

## `SADESession`

Purpose: Captures a single UAV/pilot interaction lifecycle with a SADE zone (request, decision, in-zone/denied/exited state, timing, and references to related records such as environmental conditions).


| Attribute                     | Type     | Meaning                                                                                                      |
| ----------------------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| `id`                          | `str`    | Session identifier.                                                                                          |
| `pilot_id`                    | `str`    | Pilot identifier.                                                                                            |
| `uav_id`                      | `str`    | UAV identifier for this session.                                                                             |
| `sade_zone_id`                | `str`    | SADE zone identifier for this session.                                                                       |
| `mission`                     | `str?`   | Mission label/description (optional).                                                                        |
| `status`                      | `str`    | Session lifecycle state (`REQUEST`, `IN_ZONE`, `DENIED`, `EXITED`, etc.).                                    |
| `outcome`                     | `str?`   | Final/result state if kept separately from lifecycle status (e.g., `APPROVED`, `DENIED`, `ACTION_REQUIRED`). |
| `time_in`                     | `float?` | Entry time (epoch seconds, current code style).                                                              |
| `time_out`                    | `float?` | Exit time (epoch seconds).                                                                                   |
| `environmental_conditions_id` | `str?`   | One-to-one reference to `SessionEnvironmentalConditions` for this session.                                   |


