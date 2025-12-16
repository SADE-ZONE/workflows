## Status data received
The runtime monitor will receive status messages from all drones inside the SADE zone in the following format:
https://github.com/DroneResponse/Onboarding/blob/main/topics.md#drone-status-message 

Data will be received in a steady-stream of status messages from each drone.  Each status message is in JSON format (as above) and includes the UAV's ID, current location, attitude, heading, and more.

## What are we monitoring?

1. **Loss of Signal**: For each drone we need to raise an alert if a signal is not received in the past 30 seconds.
2. **Airspace Violation**: There are many types of airspace violation that we need to monitor for including the following:
   1. ***Drone flies into restricted airspace***: Each SADE zone needs to provide a list of restricted airspace.
   2. ***Drones fly directly above or below one another***: Drones must never fly directly over each other.
3. **Health**:
   1. ***Excessive vibration***: A clear indicator of low health
   2. ***Sudden changes in attitude**:
   3. ***Low battery**:
