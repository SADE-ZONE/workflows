# Flight Monitor Reference Tables

**Last Updated On:** 2026-04-22

Use this with [SADE_CONTRACT.md](./SADE_CONTRACT.md).
Unless noted otherwise, quantities, timestamps, and coordinate conventions follow [../QUANTITIES_AND_UNITS.md](../QUANTITIES_AND_UNITS.md).

## Event Types

An event is something that occurred during the flight within the approved allocated time.  
For example, a `FLIGHT_SEGMENT`, `EXIT_REQUEST`, or an `INCIDENT`.


| **Event Type**   | **Meaning**                     | **Current Required Fields**                                                    |
| ---------------- | ------------------------------- | ------------------------------------------------------------------------------ |
| `FLIGHT_SEGMENT` | One contiguous flown interval.  | `type`, `time_in_utc`, `time_out_utc`, `battery_state_in`, `battery_state_out` |
| `EXIT_REQUEST`   | Operator intent to leave early. | `type`, `time_utc`, `reason`                                                   |
| `INCIDENT`       | One coded incident.             | `type`, `time_utc`, `incident_code`                                            |


### `FLIGHT_SEGMENT`

Meaning: one contiguous flown interval.

At least one `FLIGHT_SEGMENT` event must be present for tracker finalization.

Expected JSON

```json
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
}
```



### `EXIT_REQUEST`

Meaning: operator intent to leave early.

Expected JSON

```json
{
  "type": "EXIT_REQUEST",
  "time_utc": "2026-03-09T18:35:00Z",
  "reason": "Returning home early"
}
```



### `INCIDENT`

Meaning: one coded incident.

Expected JSON

```json
{
  "type": "INCIDENT",
  "time_utc": "2026-03-09T18:41:00Z",
  "incident_code": "0101-100"
}
```



## Incident Codes

`incident_code` is the specific classification attached to an `INCIDENT` event.  
So:

- `type = INCIDENT` tells you this event is an incident
- `incident_code` tells you which incident it was

Incidents are a list of strings in format `hhhh-sss`, where:

- `hhhh` = high-level code
- `sss` = sub-code (3 digits)


| **High-Level Code** | **High-Level Category**           | **Sub-Code** | **Subcategory**                                              |
| ------------------- | --------------------------------- | ------------ | ------------------------------------------------------------ |
| 0001                | Injury-Related Incidents          | 001          | Serious Injury (Hospitalization, Fracture, Organ Damage)     |
| 0001                | Injury-Related Incidents          | 010          | Loss of Consciousness                                        |
| 0010                | Property Damage                   | 001          | Damage > $500 (Property Not Owned by Operator)               |
| 0011                | Mid-Air Collisions / Near-Misses  | 001          | Collision with Manned Aircraft                               |
| 0011                | Mid-Air Collisions / Near-Misses  | 010          | Near Mid-Air Collision (NMAC)                                |
| 0100                | Loss of Control / Malfunctions    | 001          | GPS or Navigation Failure                                    |
| 0100                | Loss of Control / Malfunctions    | 010          | Flight Control Failure                                       |
| 0100                | Loss of Control / Malfunctions    | 011          | Battery Failure / Fire                                       |
| 0100                | Loss of Control / Malfunctions    | 100          | Communication Loss (C2 Link)                                 |
| 0100                | Loss of Control / Malfunctions    | 101          | Flyaway (Uncontrolled Drone)                                 |
| 0101                | Airspace Violations               | 001          | Unauthorized Entry into Controlled Airspace                  |
| 0101                | Airspace Violations               | 010          | Violation of Temporary Flight Restriction (TFR)              |
| 0101                | Airspace Violations               | 011          | Overflight of People Without Waiver                          |
| 0101                | Airspace Violations               | 100          | Night Operations Without Proper Lighting                     |
| 0110                | Security & Law Enforcement Events | 001          | Intercepted by Law Enforcement or Military                   |
| 0110                | Security & Law Enforcement Events | 010          | Suspected Cyberattack or GPS Jamming                         |
| 0110                | Security & Law Enforcement Events | 011          | Drone Used in Criminal Activity                              |
| 1111                | Incomplete Flight Log             | 001          | (Following subsequent investigation) Drone did not exit zone |


## Payload Component Types

`declared_payload.components` should use one typed code per component:


| **Type**     | **Meaning**                      |
| ------------ | -------------------------------- |
| `CAMERA_01`  | Standard RGB photo/video camera  |
| `CAMERA_10`  | Mapping or photogrammetry camera |
| `CAMERA_11`  | Zoom or inspection camera        |
| `THERMAL_01` | Thermal imaging camera           |
| `LIDAR_01`   | LiDAR payload                    |
| `OTHER_000`  | Other or unspecified payload     |


