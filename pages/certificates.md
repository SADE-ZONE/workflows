# Drone Certificates: 
This page lists the types of certificates that will be implemented on the SafeCert software (INCLUDE URL). They are organized as follows: 

> ## Headings are master certificates
> A master certificate is only valid if all of the certificates in the bullets below them are valid.
> - (C, {NI}) `<Certificate_Name>`: A (C) indicates that `Certificate_Name` is a certificate. *NI* indicates that the certificate is Not Implemented yet. 
>   - (V, type, {I, E}) `<variable_name>`: (V) indicates this bullet represents a variable. The *type* of the variable can be one of {int, float, string, bool, list}. The letter *I* or *E* represents whether the variable is an Internal variable or an External variable. External variables are sent by the SADE zone or other software to SafeCert. Internal variables are entered by the operator into SafeCert themselves. 
>   - (C) `<Sub_Certificate_Name>`: A (C) within another certificate is functioning as a sub-certificate. The sub-certificates must all be valid for the higher-level certificates to be valid. 
>   - (V) `<sub_variable_name>`: A (V) within another (V) means that the higher-level variable can be calculated from the sub-variables.
> 
> If a certificate appears in more than one location, it will be noted and will require the same variables as the first instance.

## Aviation or Performance certificates
These certificates are based on the ability of the drone to fly. 

- (C, NI) `<Weather>`: Inclement weather certificate (rain, sleet, hail, fog, air quality)
    - (V, list[string], I) `<restricted_weather_conditions>`: A list of restricted types of weather conditions (list of strings)
    - (V, string, E) Current weather conditions
- (C) `<Wind>`: 
    - (V, float, I) `<drone_max_wind_speed>`: The drone's maximum allowed wind speed
    - (V, float, I) `<pilot_wind_ability>`: The pilot's comfort level with wind speed, as represented by the allowed percentage of max wind speed [0% to 100%]
    - (V, float, E) `<current_wind_speed>`
- (C): Temperature
    - (V, float, I) `<min_temp>`: Min temp allowed by the drone
    - (V, float, I) `<max_temp>`: Max temp allowed by the drone
    - (V, float, E) `<current_temp>`: Current temp
- (C): `<Density_Altitude>`
    - (V, int, I) `<drone_max_density_altitude>`: Max density altitude (or just max altitude) allowed by drone
    - (V, int, E) `<current_density_altitude>`: Current density altitude - can be calculated using:
        - (V, int, E) `<current_altitude>`: Current altitude at the SADE location (above MSL) *(NB: Should this relate to the max altitude in the SADE zone?)*
        - (V, int, E) `<current_temp>`: Current temperature
        - (V, int, E) `<current_pressure>`: Current air pressure
- (C, NI) `<Light_Conditions>`
    - (V, list[string], I) `<restricted_lighting_conditions>`: A list of restricted ligthing conditions (list of strings) 
    - (V, string, E) `<current_lighting_conditions>`: A string representing the current light conditions
- (C) `<Payload>`: Payload requirements for the drone
    - (V, int, I) `<max_payload>`: Max payload the drone can take off with
    - (V, int, I) `<takeoff_payload>`: Actual takeoff payload for this mission.
- (C, NI) `<Self_Healing>`: Self-healing capability (in case of RNP failure, low battery, DAA failure) *(NB: This was suggested by Jane. I am not sure how to implement this yet.)*

## Navigation or (RNP) Required navigation performance certificates
These certificates judge the ability of the drone to stay on its desired track.

- (C, NI) `<Weather>`: Inclement weather (same as above)
- (C) `<Wind>`: (same as above)
- (C) `<Temperature>`: (same as above)
- (C) `<Density_Alititude>`: (same as above)
- (C) `<Proving_Ground_Wind>`: Whether the drone has passed the wind portion of the proving ground test. *(NB: I am not sure how this will work yet)*
    - (V, bool, E) `<proving_ground_result>`: Proving ground result - Pass or Fail on the wind ability from the proving ground.
- (C, NI) `<GPS>`: GPS *(NB: I am not sure how this will work yet)*
    - (V, bool, I) `<has_gps>`: Whether the drone has a GPS system
    - (V, string, I) `<gps_type>`: GPS/GNSS type and version number
    - (V, list[string], E) `<allowed_gps_types>`: Allowed GPS/GNSS types and version numbers
- (C) `<Safe_Navigation>`: Ability to avoid aircraft/obstacles
    - (C) `<DAA>`: Detect and Avoid (DAA) system:
        - (V, bool, I) `<has_daa>`: Has a functioning DAA system
    - (C, NI) `<Navigation_Software>`: Has working navigation software. *(NB: Not sure how we want to implement this.)*
    - (C, NI) `<Camera>`: Has a working camera and camera connection. *(NB: Not sure how we want to implement this.)*
    - (C, NI) `<Geolocation>`: Geolocation using computer vision. *(NB: Not sure how we want to implement this.)*

## Communication capability (including SADE zone requirements?)
These certificates are based on the ability of the drone and operator to communicate to the SADE zone correctly, and to abide by the SADE zone's requirements. 

- (C, NI) `<Base_Station_Connection>`: Reliable radio connection to base station
- (C) `<SADE_Zone_Requirements>`: SADE Zone requirements
    - (C) `<SADE_Communication>`: Ability to communicate to SADE zone
        - (V, string, I) `<comm_software_version>`: Communication software version
        - (V, list[string], E) `<allowed_comm_software_version>`: Allowed communication software versions
    - (V, bool, I) `<can_detect_adsb>`: Able to detect ADS-B signals (but will not broadcast)
    - (C, NI) `<Payload_SADE>`: Payload requirements for SADE zone - *(NB: Not sure how we want to implement this.)*
    - (C, NI) `<Cloud_Access>`: “Cloud” access - *(NB: Not sure how we want to implement this.)*
    - (C, NI) `<Air_Leasing>`: Capability for SADE air leasing - *(NB: Not sure how we want to implement this.)*

## Operator Certificates:
These certificates are based on the operator's certifications and preparations for the flight. 

- (C) `<Part 107>`: Does the pilot have a part 107 (or equivalent) license
    - (V, bool, I): Whether the pilot has a Part 107 certificate. *(NB: This could also be the date of the last certification, and we check to see if that has been in the last 24 months.)*
- (C) `<BVLOS>`: Is the drone flying BVLOS? Can it fly BVLOS? *(NB: all of the variables in this certificate are currently boolean. This is basically a checklist of whether you will do these things. This could change in the future.)*
    - (C) `<BVLOS_Equipment>`:
        - (V, bool, I) `<adsb_receive>`: Be able to receive ADS-B signals (either on board or on the ground)
        - (V, bool, I) `<detect_and_avoid>`: Have a functioning Detect and Avoid system on board
        - (V, bool, I) `<remote_id>`: Have functioning Remote ID that can transmit a BVLOS status message
        - (V, bool, I) `<lighting>`: Have functioning anti-collision lighting onboard the aircraft
        - (V, bool, I) `<safe_and_airworthy>`: The UAS must be in a safe and airworthy condition
    - (C) `<BVLOS_Operational_Rules>`:
        - (V, bool, I) `<avoid_people>`: Avoid areas with large numbers of people on the ground
        - (V, bool, I) `<notams>`: Have knowledge of NOTAMS and airspace along entire route
        - (V, bool, I) `<yield_right_of_way>`: Yield right-of-way to aircraft broadcasting ADS-B Out
        - (V, bool, I) `<avoid_air_traffic>`: Avoid all high-traffic areas for other aircraft (such as airports, etc.)
    - (C) `<Operator_Requirements>`:
        - (V, bool, I) `<bvlos_training>`: The operator should have received training on safe BVLOS flying. 
        - (V, bool, I) `<backup_landing>`: The operator should have backup landing sites along the planned flight path.
- (C) `<Observers>`: Certificate related the flight observers (if required)
    - (V, bool, I) `<has_observers>`: Whether the flight has observers. 