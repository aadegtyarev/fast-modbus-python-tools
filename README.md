# Python-utility for Fast Modbus from Wiren Board

## Overview
This repository provides a set of Python scripts for efficient interaction and event configuration in Modbus networks. These tools enable working with devices supporting Fast Modbus: scanning, reading, and configuring events. Additionally, it allows for reading and writing standard Modbus registers using the Fast Modbus protocol and serial number addressing.

## Installation
These tools require Python 3.8 or higher.
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/fast-modbus-python-tools.git
   ```
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt

## Tool Descriptions

### General Modbus Client
The `fast-modbus-client.py` script allows read and write access to Modbus registers. It supports:
- Reading one or multiple registers.
- Writing data to registers.
- Displaying register values in either decimal or hexadecimal format.

#### Arguments:
- `--device`: Specifies the serial device (e.g., `/dev/ttyUSB0`).
- `--baud`: Baud rate for Modbus communication. Default is 9600.
- `--slave_id`: Modbus ID of the target device.
- `--read`: Range of registers to read (format: `start:end`).
- `--write`: Write a value to a register (format: `address:value`).
- `--output`: Format for output, either `decimal` or `hex`.
- `--debug`: Enables debug output for troubleshooting.

To see all arguments, use:
```bash
python fast-modbus-client.py --help
```

**Example Usage**:
```bash
python fast-modbus-client.py --device /dev/ttyACM0 --baud 9600 --slave_id 126 --read 1:10 --output hex
```

### Event Configuration Tool
The `fast-modbus-config-events.py` script configures event notifications for Modbus registers, enabling and disabling event notifications for the following types:
- `coil`, `discrete`, `holding`, and `input` registers.
- Setting priorities for event notifications to help manage traffic on the Modbus network.

#### Arguments:
- `--device`: Specifies the serial device (e.g., `/dev/ttyUSB0`).
- `--baud`: Baud rate for Modbus communication. Default is 9600.
- `--slave_id`: Modbus ID of the target device.
- `--config`: Configuration string (format: `register_type:address:count:priority`), supports multiple configurations separated by commas.
- `--debug`: Enables debug output for troubleshooting.

To see all arguments, use:
```bash
python fast-modbus-config-events.py --help
```

**Example Usage**:
```bash
python fast-modbus-config-events.py --device /dev/ttyACM0 --baud 9600 --slave_id 126 --config "discrete:0:2:1,holding:5:2:2" --debug
```

### Event Data Reader
The `fast-modbus-events.py` script fetches and parses event data from Modbus devices to provide structured insights into register changes. It’s particularly useful for monitoring and debugging event-driven updates from Modbus registers.

#### Arguments:
- `--device`: Specifies the serial device (e.g., `/dev/ttyUSB0`).
- `--baud`: Baud rate for Modbus communication. Default is 9600.
- `--flag`: Event confirmation flag, used to manage event processing.
- `--debug`: Enables debug output for troubleshooting.

To see all arguments, use:
```bash
python fast-modbus-events.py --help
```

**Example Usage**:
```bash
python fast-modbus-events.py --device /dev/ttyACM0 --baud 9600 --flag 0x00 --debug
```

### Device Scanner
The `fast-modbus-scanner.py` script scans the Modbus network for active devices, detecting and displaying device IDs. It includes configuration options for various baud rates and provides detailed debugging output.

#### Arguments:
- `--device`: Specifies the serial device (e.g., `/dev/ttyUSB0`).
- `--baud`: Baud rate for Modbus communication. Default is 9600.
- `--debug`: Enables debug output for troubleshooting.

To see all arguments, use:
```bash
python fast-modbus-scanner.py --help
```

**Example Usage**:
```bash
python fast-modbus-scanner.py --device /dev/ttyACM0 --baud 9600 --debug
```

## Contribution
We welcome community contributions to improve these tools! If you have ideas or fixes, please create a pull request with a description of your changes. Before submitting, make sure the code follows the repository's style and is thoroughly tested.
