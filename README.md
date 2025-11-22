# ThingsBoard IoT Virtual Sensor Simulator

A Python-based virtual sensor simulator for **ThingsBoard** that publishes temperature and humidity telemetry via MQTT and responds to dynamic shared attribute updates.

## Features

- **MQTT Connectivity**: Connects to ThingsBoard cloud using paho-mqtt
- **Telemetry Publishing**: Sends temperature and humidity data at configurable intervals
- **Shared Attributes Support**: Dynamically updates behavior from ThingsBoard
  - `interval` (seconds): Controls telemetry publish frequency (default: 5)
  - `enabled` (boolean): Pause/resume sensor operation (default: true)
  - `firmware_version` (string): Simulate OTA updates (default: 1.0)
- **Reconnection Handling**: Automatic reconnection with exponential backoff
- **Logging**: Comprehensive logging to console and file (`sensor.log`)
- **Graceful Shutdown**: Handles Ctrl+C interrupts cleanly

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `paho-mqtt==1.6.1` - MQTT client library for Python

### 2. Run the Sensor

#### Normal Mode (Connect to ThingsBoard)

```bash
python sensor.py
```

````

The sensor will:

1. Connect to ThingsBoard MQTT broker (eu1.cloud.thingsboard.io:1883) - _or simulate in mock mode_
2. Authenticate using device access token: `PokI1pbzWiZY2OvMdmTi`
3. Request current shared attributes (mock: auto-load defaults)
4. Begin publishing telemetry data every 5 seconds (or configured interval)
5. Log all activity to console and `sensor.log`

**To stop**: Press `Ctrl+C` for graceful shutdown.

## Configuration

### MQTT Connection Details

| Parameter        | Value                    |
| ---------------- | ------------------------ |
| **Host**         | eu1.cloud.thingsboard.io |
| **Port**         | 1883                     |
| **Device Name**  | ##         |
| **Access Token** | ##     |

To modify these settings, edit the constants at the top of `sensor.py`:

```python
THINGSBOARD_HOST = "eu1.cloud.thingsboard.io"
THINGSBOARD_PORT = 1883
DEVICE_ACCESS_TOKEN = "##"
DEVICE_NAME = "##"
````

## Telemetry Data

The sensor publishes the following telemetry:

```json
{
  "temperature": 22.45,
  "humidity": 55.32
}
```

- **Temperature**: Float value (°C), range ~15-25°C with random variations
- **Humidity**: Float value (%), range ~35-65% with random variations
- **Publish Frequency**: Every `interval` seconds (configurable via shared attributes)

## Shared Attributes

Configure the sensor behavior by setting shared attributes in ThingsBoard. To set shared attributes:

### Via ThingsBoard Dashboard

1. Navigate to **Devices** → **VirtualSensor01**
2. Click **Shared Attributes** tab
3. Set the following attributes:

| Attribute          | Type    | Default | Description                               |
| ------------------ | ------- | ------- | ----------------------------------------- |
| `interval`         | Integer | 5       | Telemetry publish interval in seconds     |
| `enabled`          | Boolean | true    | Enable/disable sensor operation           |
| `firmware_version` | String  | 1.0     | Current firmware version (OTA simulation) |

#### Example Configuration

```json
{
  "interval": 10,
  "enabled": true,
  "firmware_version": "1.2"
}
```

### Via REST API (Alternative)

```bash
curl -X POST "https://eu1.cloud.thingsboard.io/api/plugins/telemetry/DEVICE_ID/attributes/SHARED_SCOPE" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interval": 10,
    "enabled": true,
    "firmware_version": "1.2"
  }'
```

## Dashboard Setup

### Step 1: Create Dashboard

1. In ThingsBoard, go to **Dashboards** → **Create new dashboard**
2. Name it: `VirtualSensor01 Dashboard`
3. Click **Create**

### Step 2: Add Gauge for Temperature

1. Click **Edit dashboard** (pencil icon)
2. Click **Add new widget** → **Gauges** → **Simple gauge**
3. Configure:
   - **Datasource**: VirtualSensor01
   - **Data key**: temperature
   - **Title**: Temperature
   - **Min value**: 0
   - **Max value**: 40
   - **Unit**: °C

### Step 3: Add Gauge for Humidity

1. Click **Add new widget** → **Gauges** → **Simple gauge**
2. Configure:
   - **Datasource**: VirtualSensor01
   - **Data key**: humidity
   - **Title**: Humidity
   - **Min value**: 0
   - **Max value**: 100
   - **Unit**: %

### Step 4: Add Time-Series Chart

1. Click **Add new widget** → **Charts** → **Timeseries**
2. Configure:
   - **Datasource**: VirtualSensor01
   - **Data keys**: temperature, humidity
   - **Title**: Temperature & Humidity Over Time
   - **Time window**: Last hour (or preferred range)
3. Arrange widgets on dashboard

### Step 5: Add Attribute Controls (Optional)

1. Click **Add new widget** → **Input widgets** → **Number input** (for interval)
2. Configure:

   - **Target**: VirtualSensor01 → Shared Attributes
   - **Attribute**: interval
   - **Label**: Interval (seconds)

3. Repeat for `enabled` (boolean toggle) and `firmware_version` (text input)

4. Save dashboard

## Dashboard Screenshots

> **TODO**: Add the following screenshots to your documentation:
>
> 1. **Dashboard Overview** - Complete dashboard with 2 gauges and time-series chart
> 2. **Temperature Gauge** - Showing live temperature reading
> 3. **Humidity Gauge** - Showing live humidity reading
> 4. **Time-Series Chart** - Historical temperature and humidity data
> 5. **Shared Attributes Panel** - Configuration of interval, enabled, and firmware_version
> 6. **Sensor Logs** - Console output showing telemetry published and attributes updated

## Logging

The sensor logs to both console and `sensor.log` file. Log levels include:

- **INFO**: Successful operations (connect, telemetry publish, attribute updates)
- **WARNING**: Connection issues, reconnection attempts
- **ERROR**: Failed operations, exceptions

Example log output:

```
2025-11-22 10:15:32,123 - VirtualSensor01 - INFO - Starting VirtualSensor01 - Connecting to eu1.cloud.thingsboard.io:1883
2025-11-22 10:15:34,456 - VirtualSensor01 - INFO - Connected to ThingsBoard successfully
2025-11-22 10:15:34,789 - VirtualSensor01 - INFO - Subscribed to v1/devices/me/attributes
2025-11-22 10:15:35,012 - VirtualSensor01 - INFO - Requested shared attributes
2025-11-22 10:15:35,234 - VirtualSensor01 - INFO - Published telemetry: {'temperature': 21.45, 'humidity': 52.34}
2025-11-22 10:15:40,345 - VirtualSensor01 - INFO - Published telemetry: {'temperature': 22.12, 'humidity': 51.89}
```
