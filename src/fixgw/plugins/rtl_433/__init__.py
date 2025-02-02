import subprocess
import json
import sys
import time
import yaml
import threading
import fixgw.plugin as plugin
import random
from collections import OrderedDict

def convert_type(value, dtype):
    """Convert value to the specified data type."""
    try:
        if dtype == "int":
            return int(value)
        elif dtype == "float":
            return float(value)
        elif dtype == "bool":
            return bool(value)
        elif dtype == "string":
            return str(value)
    except ValueError:
        print(f"Warning: Could not convert {value} to {dtype}")
    return value  # Return unmodified if conversion fails

def apply_transform(value, transform):
    """Apply scale, offset, rounding, and threshold transformations to data."""
    if value is None:
        return None
    if "threshold" in transform:
        value = 1 if value > transform["threshold"] else 0
    else:
        value = (value * transform.get("scale", 1)) + transform.get("offset", 0)
        if "round" in transform:
            value = round(value, transform["round"])
    
    # Apply type conversion if specified
    if "type" in transform:
        value = convert_type(value, transform["type"])
    
    return value

def map_data(json_data, parent):
    """Map rtl_433 JSON data to application fixids based on YAML config."""
    sensor_id = json_data.get("id")
    if sensor_id not in parent.status["Devices Seen"]:
        parent.status["Devices Seen"][sensor_id] = 1
    else:
        parent.status["Devices Seen"][sensor_id] += 1
    for sensor in parent.config["sensors"]:
        if sensor["sensor_id"] == sensor_id:
            mappings = sensor["mappings"]
            for fixid, rules in mappings.items():
                source_key = rules["source"]
                if source_key in json_data:
                    value = apply_transform(json_data[source_key], rules)
                    parent.db_write(fixid, value)
            return

def process_json(data, parent):
    """Process each JSON data string received from rtl_433"""
    try:
        parsed_data = json.loads(data)
        map_data(parsed_data, parent)
    except json.JSONDecodeError:
        print("Error decoding JSON:", data)

def start_rtl_433(simulate=False):
    """Start rtl_433 process with JSON output, or simulate it."""
    if simulate:
        return None  # Indicate simulation mode
    process = subprocess.Popen(
        ["rtl_433", "-F", "json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line-buffered output
    )
    return process

def generate_mock_data(config):
    """Generate simulated rtl_433 JSON output."""
    while True:
        for sensor in config["sensors"]:
            data = {
                "id": sensor["sensor_id"],
                "pressure_kPa": random.uniform(200, 300),
                "temperature_C": random.uniform(15, 35),
                "battery_V": random.uniform(2.0, 3.5)
            }
            yield json.dumps(data)
            time.sleep(2)  # Simulate sensor transmission interval

class MainThread(threading.Thread):
    def __init__(self, parent):
        super(MainThread, self).__init__()
        self.getout = False  # Indicator for when to stop
        self.parent = parent  # Parent plugin object
        self.simulate = self.parent.config.get("simulate", False)

    def run(self):
        config = self.parent.config
        process = start_rtl_433(simulate=self.simulate)
        if process:
            self.parent.status["rtl_433 pid"] = process.pid
        
        def stop_rtl_433(signum=None, frame=None):
            print("Stopping rtl_433...")
            if process:
                process.terminate()
                process.wait()
            sys.exit(0)
        
        if self.simulate:
            mock_generator = generate_mock_data(config)
            while not self.getout:
                process_json(next(mock_generator), self.parent)
        else:
            while not self.getout:
                line = process.stdout.readline()
                if not line:
                    print("rtl_433 exited unexpectedly. Restarting...")
                    process = start_rtl_433()
                    if process:
                        self.parent.status["rtl_433 pid"] = process.pid
                    continue
                process_json(line.strip(), self.parent)

    def stop(self):
        self.getout = True

class Plugin(plugin.PluginBase):
    def __init__(self, name, config):
        super(Plugin, self).__init__(name, config)
        self.thread = MainThread(self)
        self.status = OrderedDict()
        self.status["Devices Seen"] = OrderedDict()
        self.status["rtl_433 pid"] = None

    def run(self):
        self.thread.start()

    def stop(self):
        self.thread.stop()
        if self.thread.is_alive():
            self.thread.join(1.0)
        if self.thread.is_alive():
            raise plugin.PluginFail

    def get_status(self):
        return self.status

