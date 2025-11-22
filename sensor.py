#!/usr/bin/env python3
"""
ThingsBoard IoT Virtual Sensor Simulator
Simulates a temperature and humidity sensor with dynamic configuration
via shared attributes (interval, enabled, firmware_version).
"""

import json
import logging
import random
import sys
import time
from threading import Thread, Event
from typing import Dict, Any

import paho.mqtt.client as mqtt

# Configuration
THINGSBOARD_HOST = "eu.thingsboard.cloud"
THINGSBOARD_PORT = 1883
DEVICE_ACCESS_TOKEN = "PokI1pbzWiZY2OvMdmTi"
DEVICE_NAME = "VirtualSensor01"

# MQTT Topics
TELEMETRY_TOPIC = "v1/devices/me/telemetry"
ATTRIBUTES_SUBSCRIBE_TOPIC = "v1/devices/me/attributes"
ATTRIBUTES_REQUEST_TOPIC = "v1/devices/me/attributes/request/1"
ATTRIBUTES_RESPONSE_TOPIC = "v1/devices/me/attributes/response/1"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sensor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(DEVICE_NAME)


class VirtualSensor:
    """ThingsBoard virtual sensor with shared attributes support."""

    def __init__(self):
        """Initialize the sensor."""
        self.client = mqtt.Client(client_id=DEVICE_NAME)
        self.client.username_pw_set(DEVICE_ACCESS_TOKEN)
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Sensor state
        self.interval = 5  # seconds
        self.enabled = True
        self.firmware_version = "1.0"
        
        # Control flags
        self.stop_event = Event()
        self.connected = False
        
        # Reconnect parameters
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info("Connected to ThingsBoard successfully")
            self.connected = True
            self.reconnect_attempts = 0
            
            # Subscribe to shared attributes updates
            client.subscribe(ATTRIBUTES_SUBSCRIBE_TOPIC)
            logger.info(f"Subscribed to {ATTRIBUTES_SUBSCRIBE_TOPIC}")
            
            # Request shared attributes on connect
            self._request_attributes()
        else:
            logger.error(f"Failed to connect, return code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection, return code {rc}")
        else:
            logger.info("Disconnected from ThingsBoard")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {msg.topic}: {payload}")
            
            # Handle shared attributes update
            if "shared" in payload:
                self._update_attributes(payload["shared"])
            # Handle attribute response
            elif "response" in payload:
                self._update_attributes(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _request_attributes(self):
        """Request shared attributes from ThingsBoard."""
        try:
            request_payload = {"clientKeys": "interval,enabled,firmware_version"}
            self.client.publish(
                ATTRIBUTES_REQUEST_TOPIC,
                json.dumps(request_payload),
                qos=1,
            )
            logger.info("Requested shared attributes")
        except Exception as e:
            logger.error(f"Failed to request attributes: {e}")

    def _update_attributes(self, attributes: Dict[str, Any]):
        """Update sensor attributes from shared attributes."""
        try:
            if "interval" in attributes:
                old_interval = self.interval
                self.interval = max(1, int(attributes["interval"]))
                if old_interval != self.interval:
                    logger.info(f"Updated interval: {old_interval}s → {self.interval}s")
            
            if "enabled" in attributes:
                old_enabled = self.enabled
                self.enabled = bool(attributes["enabled"])
                if old_enabled != self.enabled:
                    logger.info(f"Updated enabled: {old_enabled} → {self.enabled}")
            
            if "firmware_version" in attributes:
                old_version = self.firmware_version
                self.firmware_version = str(attributes["firmware_version"])
                if old_version != self.firmware_version:
                    logger.info(
                        f"Updated firmware_version: {old_version} → {self.firmware_version}"
                    )
                    self._simulate_ota()
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid attribute value: {e}")

    def _simulate_ota(self):
        """Simulate OTA (Over-The-Air) update."""
        logger.info(f"Simulating OTA update to firmware v{self.firmware_version}")
        # In a real scenario, this would trigger actual firmware download/update
        logger.info("OTA simulation completed")

    def _generate_sensor_data(self) -> Dict[str, float]:
        """Generate simulated sensor data."""
        # Base values with slight variations
        temperature = 20 + random.uniform(-5, 5) + random.random()
        humidity = 50 + random.uniform(-15, 15) + random.random()
        
        return {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
        }

    def _publish_telemetry(self):
        """Publish telemetry data to ThingsBoard."""
        if not self.connected:
            logger.warning("Not connected, skipping telemetry publish")
            return
        
        if not self.enabled:
            logger.debug("Sensor disabled, skipping telemetry")
            return
        
        try:
            data = self._generate_sensor_data()
            payload = json.dumps(data)
            
            result = self.client.publish(TELEMETRY_TOPIC, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published telemetry: {data}")
            else:
                logger.warning(f"Failed to publish (rc={result.rc}): {data}")
        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")

    def _reconnect_with_backoff(self):
        """Attempt to reconnect with exponential backoff."""
        while not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
            logger.info(
                f"Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
                f"in {wait_time}s"
            )
            
            if self.stop_event.wait(wait_time):
                # Stop was signaled during wait
                break
            
            try:
                self.client.reconnect()
                logger.info("Reconnection attempt successful")
                return
            except Exception as e:
                logger.warning(f"Reconnection attempt failed: {e}")
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")

    def _telemetry_loop(self):
        """Main telemetry publishing loop."""
        logger.info("Starting telemetry loop")
        
        while not self.stop_event.is_set():
            if not self.connected:
                self._reconnect_with_backoff()
                if not self.connected:
                    # Still not connected, wait before retrying
                    self.stop_event.wait(self.reconnect_delay)
                    continue
            
            self._publish_telemetry()
            
            # Wait for the specified interval or until stop is signaled
            self.stop_event.wait(self.interval)
        
        logger.info("Telemetry loop stopped")

    def start(self):
        """Start the sensor connection and telemetry loop."""
        try:
            logger.info(
                f"Starting {DEVICE_NAME} - Connecting to {THINGSBOARD_HOST}:{THINGSBOARD_PORT}"
            )
            
            # Connect to ThingsBoard
            self.client.connect(THINGSBOARD_HOST, THINGSBOARD_PORT, keepalive=60)
            self.client.loop_start()
            
            # Give connection time to establish
            time.sleep(2)
            
            # Start telemetry loop in a separate thread
            telemetry_thread = Thread(target=self._telemetry_loop, daemon=True)
            telemetry_thread.start()
            
            logger.info("Sensor started successfully")
            return telemetry_thread
        except Exception as e:
            logger.error(f"Failed to start sensor: {e}")
            raise

    def stop(self):
        """Stop the sensor and disconnect gracefully."""
        logger.info("Stopping sensor...")
        self.stop_event.set()
        
        try:
            # Give telemetry loop time to exit
            time.sleep(1)
            
            # Disconnect from MQTT
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Sensor stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    sensor = VirtualSensor()
    telemetry_thread = sensor.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
    finally:
        sensor.stop()
        telemetry_thread.join(timeout=5)
        logger.info("Application exited")


if __name__ == "__main__":
    main()
