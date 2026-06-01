# Current Drone Certificates: 

The following table includes the variables that SafeCert currently supports, as well as the input variables that will soon be available as inputs to certificates. 

| Certificate   | Input Variable        | Type  | Description |
| ------------- | ---------             | ----  | ----------- |
| Wind          | current_wind_speed    | float | current wind speed in (UNIT) |
| Temperature   | current_temp          | float | current temp in (UNIT) |
| Payload       | takeoff_payload       | int   | takeoff payload in (UNIT) |
| BVLOS         | NONE |
| Part_107      | NONE |


Notes:
- SafeCert will read the certificate name from "keyword" and input variables from "params".
- If a variable is included that SafeCert does not recognize, it will be ignored. For example, the "authority" variable is ignored in "BVLOS" certificates currently. 

Example json:

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
      "category": "OPERATOR",
      "requirements": [
        { 
            "expr": "PART_107", 
            "keyword": "PART_107", 
            "params": [] },
        { 
            "expr": "BVLOS", 
            "keyword": "BVLOS", 
            "params": [{ "key": "authority", "value": "FAA" }] }
      ]
    },
    {
      "category": "AVIATION",
      "requirements": [
          { "expr": "PAYLOAD(2kg)",
          "keyword": "PAYLOAD",
          "params": [{ "key": "takeoff_payload", "value": "2kg" }]
        }
      ]
    },
    {
      "category": "AVIATION",
      "requirements": [
        { 
            "expr": "WIND(28mph)", 
            "keyword": "WIND", 
            "params": [{ "key": "current_wind_speed", "value": "28mph" }] }
      ]
    }
  ]
}
```