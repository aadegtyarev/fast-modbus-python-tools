import serial
import struct
import time

def calculate_crc(data):
    """
    Calculate the CRC16 checksum for Modbus data.

    Args:
        data (bytes): The data to calculate the CRC for.

    Returns:
        int: The calculated CRC16 checksum.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def check_crc(response):
    """
    Verify the CRC checksum of the received response.

    Args:
        response (bytes): The response data to check.

    Returns:
        bool: True if the CRC is correct, False otherwise.
    """
    if len(response) < 3:
        return False
    data, received_crc = response[:-2], struct.unpack('<H', response[-2:])[0]
    return received_crc == calculate_crc(data)

def format_bytes(data):
    """
    Format bytes as a human-readable hex string.

    Args:
        data (bytes): The data to format.

    Returns:
        str: A string representation of the bytes in hexadecimal format.
    """
    return ' '.join(f"0x{byte:02X}" for byte in data)

def send_command(serial_port, command, debug=False):
    """
    Send a command to the Modbus device through the serial port.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        command (bytes): The command to send.
        debug (bool, optional): Whether to print debug information. Defaults to False.
    """
    full_command = command + struct.pack('<H', calculate_crc(command))
    if debug:
        print(f"SND: {format_bytes(full_command)}")
    serial_port.write(full_command)

def init_serial(device, baudrate):
    """
    Initialize the serial port.

    Args:
        device (str): The serial device path (e.g., '/dev/ttyUSB0').
        baudrate (int): The baudrate for the serial communication.

    Returns:
        serial.Serial: The initialized serial port object.
    """
    return serial.Serial(port=device, baudrate=baudrate, bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0)

def wait_for_response(serial_port, timeout=2):
    """
    Wait for a response from the Modbus device.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        timeout (int, optional): The maximum wait time in seconds. Defaults to 2.

    Returns:
        bool: True if data is received, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if serial_port.in_waiting > 0:
            return True
        time.sleep(0.1)
    return False

def request_device_model(serial_port, serial_number, debug=False):
    """
    Request the model of the Modbus device by reading registers 200-219.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        serial_number (int): The serial number of the device.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        str: The device model or "Invalid CRC" if the response is corrupted.
    """
    model_request = struct.pack('>BBBIBHH', 0xFD, 0x46, 0x08, serial_number, 0x03, 200, 20)
    send_command(serial_port, model_request, debug)

    if wait_for_response(serial_port):
        response = serial_port.read(256)
        if debug:
            print(f"RCV: {format_bytes(response)}")
        if check_crc(response) and len(response) >= 40:
            return response[9:29].decode('ascii').strip()
        return "Invalid CRC"
    return "Unknown"

def send_continue_scan(serial_port, scan_command, debug=False):
    """
    Send a command to continue scanning for Modbus devices.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        scan_command (int): The scan command (either 0x46 or 0x60).
        debug (bool, optional): Whether to print debug information. Defaults to False.
    """
    send_command(serial_port, struct.pack('BBB', 0xFD, scan_command, 0x02), debug)

def scan_devices(serial_port, scan_command, device, baudrate, debug=False):
    """
    Scan for Modbus devices on the network.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        scan_command (int): The scan command (either 0x46 or 0x60).
        device (str): The serial device path (e.g., '/dev/ttyUSB0').
        baudrate (int): The baudrate for the serial communication.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        None
    """
    print(f"Starting scan on port {device} with baudrate {baudrate} and scan command {hex(scan_command)}...")

    devices = []
    send_command(serial_port, struct.pack('BBB', 0xFD, scan_command, 0x01), debug)

    while wait_for_response(serial_port, 2):
        response = serial_port.read(256)
        if not response:
            break

        if debug:
            print(f"RCV: {format_bytes(response)}")

        response = response.lstrip(b'\xFF')
        if len(response) >= 10 and response[2] == 0x03:
            serial_number, modbus_id = struct.unpack('>I', response[3:7])[0], response[7]
            model = request_device_model(serial_port, serial_number, debug)
            devices.append({"serial_number": serial_number, "modbus_id": modbus_id, "model": model})
            send_continue_scan(serial_port, scan_command, debug)
        elif response[2] == 0x04:
            print("Scan complete.")
            break

    if devices:
        print("\nFound devices:")
        print("{:<15} {:<10} {:<10}".format("Serial Number", "Modbus ID", "Model"))
        print("-" * 35)
        for device in devices:
            print("{:<15} {:<10} {:<10}".format(device["serial_number"], device["modbus_id"], device["model"]))
    else:
        print("No devices found.")

def main():
    """
    Main function to parse arguments and initiate the Modbus scanning process.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Modbus Scanner Tool")
    parser.add_argument('-d', '--device', required=True, help="TTY serial device (e.g., /dev/ttyUSB0)")
    parser.add_argument('-b', '--baud', type=int, default=9600, help="Baudrate, default 9600")
    parser.add_argument('--command', choices=['0x46', '0x60'], default='0x46', help="Scan command (0x46 or 0x60)")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    args = parser.parse_args()

    scan_command = 0x46 if args.command == '0x46' else 0x60
    serial_port = init_serial(args.device, args.baud)
    scan_devices(serial_port, scan_command, args.device, args.baud, debug=args.debug)
    serial_port.close()

if __name__ == "__main__":
    main()
