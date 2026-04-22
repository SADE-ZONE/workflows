# Quantities And Units (SADE Prototype)

**Last Updated On:** 2026-04-21

This document defines the canonical units and numeric representations for business quantities used across SADE client APIs, external-service contracts, database schema, and stored JSON payloads.

## General Rules

1. New structured numeric quantity fields should include their unit in the field name when practical.
2. Canonical structured SADE values use metric for distance, altitude, and mass.
3. Canonical structured SADE values use Fahrenheit for temperature.
4. Canonical structured SADE values use knots for wind.
5. Canonical structured SADE values use nautical miles for visibility.
6. JSON timestamps use UTC RFC3339 / ISO-8601 strings with a trailing `Z`.
7. Postgres timestamps use `TIMESTAMPTZ`.
8. GeoJSON coordinates use WGS84 `[longitude, latitude]` decimal degrees.
9. Unit conversion should happen at system boundaries, not ad hoc inside downstream business logic.

## Canonical Representation

### Naming Conventions

Use the business meaning first, then the canonical unit or representation suffix.

Canonical suffix rules:

- `_m`: meters, for example `altitude_ceiling_m`
- `_kg`: kilograms, for example `max_payload_cap_kg`
- `_f`: degrees Fahrenheit, for example `max_temp_f`
- `_knots`: knots, for example `max_wind_knots`
- `_nm`: nautical miles, for example `visibility_min_nm`
- `_pct`: percentage on a `0..100` scale, for example `battery_end_pct`
- `_v`: volts, for example `battery_voltage_end_v`
- `_ratio`: unitless ratio, typically normalized to `[0.0, 1.0]`, for example `confidence_ratio`
- `_utc`: UTC RFC3339 / ISO-8601 timestamp string with trailing `Z` in JSON, or the same semantic value stored as `TIMESTAMPTZ` in Postgres, for example `request_time_utc`
- `_geojson`: GeoJSON object using WGS84 coordinates in `[longitude, latitude]` order, for example `polygon_geojson`

Additional naming rules:

- Prefer `*_min_`* and `*_max_`* for bounded numeric ranges.
- Prefer explicit names such as `actual_start_time_utc` over ambiguous names such as `start_utc`.
- Do not omit the unit suffix from new structured quantity fields.
- Do not encode alternate units in parallel field names unless there is a clear boundary-conversion need.

### Canonical Quantities

#### Temporal


| Concept                                        | Canonical Representation                                                           | Applies To                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Business timestamps and time-window boundaries | UTC RFC3339 / ISO-8601 string with trailing `Z`. Example: `"2026-03-09T17:55:00Z"` | `requested_entry_time_utc`, `requested_exit_time_utc`, `request_time_utc`, `actual_start_time_utc`, `actual_end_time_utc`, `report_time_utc`, `window_start_utc`, `window_end_utc`, `observed_at_utc`, `generated_at_utc`, `submitted_at_utc`, `submission_time_utc`, `completed_at_utc`, `received_at_utc`, `issued_at_utc`, `expires_at_utc`, `created_at_utc`, `updated_at_utc`, `available_at_utc`, `processing_started_at_utc`, `time_in_utc`, `time_out_utc` |


#### Geospatial And Airspace


| Concept                  | Canonical Unit / Representation       | Applies To                                                                 | Notes                                                                                                                         |
| ------------------------ | ------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Zone polygon coordinates | GeoJSON WGS84 lon/lat decimal degrees | `polygon_geojson.coordinates`, `polygon_geojson`                           | Coordinate order is `[longitude, latitude]`, not `[latitude, longitude]`.                                                     |
| Altitude values          | meters                                | `altitude_ceiling_m`, `altitude_min_m`, `altitude_max_m`, `MAX_ALTITUDE_M` | This document standardizes unit only. Altitude reference frame such as AGL or MSL must be documented separately where needed. |


#### Weather And Environmental


| Concept                                 | Canonical Unit / Representation | Applies To                                   | Notes             |
| --------------------------------------- | ------------------------------- | -------------------------------------------- | ----------------- |
| Sustained wind speed and wind tolerance | knots                           | `max_wind_knots`, `max_wind_tolerance_knots` |                   |
| Wind gust speed                         | knots                           | `max_gust_knots`                             |                   |
| Visibility                              | nautical miles                  | `visibility_min_nm`                          |                   |
| Temperature                             | degrees Fahrenheit              | `min_temp_f`, `max_temp_f`                   |                   |
| Weather confidence                      | unitless ratio in `[0.0, 1.0]`  | `confidence_ratio`                           | Not a percentage. |


`precipitation_summary` is categorical text and does not carry a numeric unit.

#### Payload And Mass


| Concept                                | Canonical Unit / Representation | Applies To                                                                                                       | Notes                                                                                                                                                                   |
| -------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Payload capacity or payload mass limit | kilograms                       | current `max_payload_cap_kg` concept, payload-weight requirements when normalized into structured numeric fields | External and regulatory interfaces may still express mass in pounds or in free-form strings. Structured SADE numeric fields should normalize payload mass to kilograms. |


#### Telemetry And Electrical


| Concept                                | Canonical Unit / Representation | Applies To                                         | Notes                                                                                  |
| -------------------------------------- | ------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Telemetry altitude minimum and maximum | meters                          | `altitude_min_m`, `altitude_max_m`                 | Prefer paired `altitude_min_m` / `altitude_max_m` naming for min/max telemetry values. |
| Battery state of charge                | percent on a `0..100` scale     | `battery_start_pct`, `battery_end_pct`             | Stored as numeric percentage, not ratio.                                               |
| Battery voltage                        | volts                           | `battery_voltage_start_v`, `battery_voltage_end_v` |                                                                                        |


## External Or Opaque Expression Strings

The repo currently includes unit-bearing strings in evidence and attestation examples, such as:

- `PAYLOAD(weight<=2kg)`
- `MAX_WIND_GUST(28mph)`
- `observed_max_wind_gust: "24mph"`

These strings are not SADE's canonical internal unit model. They should be treated as opaque unless SADE explicitly parses and normalizes them.

If SADE later materializes those values into structured numeric fields:

- payload mass should normalize to kilograms
- wind and gust values should normalize to knots

## Current Cleanup Targets

These are current repo inconsistencies against the standard above:

- altitude reference frame is still not formally documented as AGL, MSL, or another standard; see the design note in [ZONE_CEILING_REFERENCE_MODEL.md](/Users/tonyalarcon/repos/sade/sade-prototype/documentation/dev/ZONE_CEILING_REFERENCE_MODEL.md)
- external evidence and attestation examples still carry unit-bearing strings such as `28mph` and `2kg`, which remain opaque unless normalized
