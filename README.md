# Python Scripts for Fast Modbus
! This repository is not affiliated with and not supported by Wiren Board. 

These tools allow interaction with devices supporting Fast Modbus: scanning, reading, and configuring events. Additionally, they enable reading and writing standard Modbus registers using the Fast Modbus protocol and addressing by serial number.
![image](https://github.com/user-attachments/assets/3224c23f-6aa8-4f89-988a-cdeafebde028)

There is also a library for working with Fast Modbus https://github.com/aadegtyarev/fast-modbus-python-library
## Script Overview

1. **fast-modbus-client.py**  
   Allows reading and writing of arbitrary registers. Specify the device's serial number, Modbus command, and register details as arguments.

   ### Parameters:
   - `-d, --device`: TTY serial device path (e.g., `/dev/ttyUSB0`).
   - `-b, --baud`: Baud rate, default is `9600`.
   - `-s, --serial`: Device serial number (decimal or hexadecimal format).
   - `-c, --command`: Modbus command (decimal or hexadecimal).
   - `-r, --register`: Register number to read/write (decimal or hexadecimal).
   - `-n, --count`: Number of registers to read (default `1`).
   - `-w, --write`: Values to write (for write operations, decimal or hexadecimal).
   - `--debug`: Enables debug output.
   - `--decimal-output`: Displays register values in decimal format.

   ### Usage Examples:
   - **Reading Registers**:
     ```bash
     python fast-modbus-client.py -d /dev/ttyUSB0 -b 9600 -s 12345 -c 3 -r 200 -n 5
     ```
   - **Writing to Registers**:
     ```bash
     python fast-modbus-client.py -d /dev/ttyUSB0 -b 9600 -s 12345 -c 16 -r 200 -w 100 200 300 --decimal-output
     ```

2. **fast-modbus-scanner.py**  
   Scans the Modbus network to identify connected devices. Retrieves device information, including model, using Fast Modbus commands.

   ### Parameters:
   - `-d, --device`: TTY serial device path (e.g., `/dev/ttyUSB0`).
   - `-b, --baud`: Baud rate, default is `9600`.
   - `--command`: Scan command (`0x46` or `0x60`, default is `0x46`).
   - `--debug`: Enables debug output.

   ### Usage Example:
   ```bash
   python fast-modbus-scanner.py -d /dev/ttyUSB0 -b 9600 --command 0x46
   ```

3. **fast-modbus-events.py**  
   Reads event data from a specified device, supporting detailed flag and length configuration for each event read.

   ### Parameters:
   - `-d, --device`: TTY serial device path (e.g., `/dev/ttyUSB0`).
   - `-b, --baud`: Baud rate, default is `9600`.
   - `--min_slave_id`: Minimum slave ID to start responding, default is `1`.
   - `--max_data_length`: Maximum length of event data, default is `100`.
   - `--slave_id`: Slave ID of the device from which the last packet was received.
   - `--flag`: Flag confirming the previous packet received.
   - `--debug`: Enables debug output.

   ### Usage Example:
   ```bash
   python fast-modbus-events.py -d /dev/ttyUSB0 -b 9600 --min_slave_id 1 --max_data_length 50 --slave_id 10 --flag 1 --debug
   ```

4. **fast-modbus-config-events.py**  
   Configures event settings for u16 registers on Modbus devices. Allows for multiple register types (e.g., discrete, input) and priority settings.

   ### Parameters:
   - `--device`: TTY serial device path (e.g., `/dev/ttyUSB0`).
   - `--baud`: Baud rate, default is `9600`.
   - `--slave_id`: Modbus device slave ID.
   - `--config`: Configuration string specifying register ranges (e.g., `input:60:2:1,discrete:0:8:1`).
   - `--debug`: Enables debug output.

   ### Usage Example:
   ```bash
   python fast-modbus-config-events.py --device /dev/ttyUSB0 --baud 9600 --slave_id 5 --config "input:60:2:1,discrete:0:8:1" --debug
   ```

## Contributing

Initial code generated with assistance from OpenAI's ChatGPT. Contributions and improvements are welcome! Feel free to submit pull requests to improve functionality or documentation.
