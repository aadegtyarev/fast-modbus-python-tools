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
    return len(response) >= 3 and struct.unpack('<H', response[-2:])[0] == calculate_crc(response[:-2])

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

def parse_event_response(response, debug=False):
    """
    Parse the event response from the Modbus device and print it in a structured format.

    Args:
        response (bytes): The raw response data from the Modbus device.
        debug (bool, optional): Whether to print debug information. Defaults to False.
    """
    # Handle the case when there are no events
    if len(response) < 7:
        print("NO EVENTS")
        return

    if len(response) < 12:
        print("[error] Response too short to be valid")
        return

    # Parse the response structure
    device_id = response[0]
    command = response[1]
    subcommand = response[2]
    flag = response[3]
    event_count = response[4]
    event_data_len = struct.unpack('>H', response[5:7])[0]  # event data length
    event_type = struct.unpack('>H', response[7:9])[0]
    event_payload = struct.unpack('>H', response[9:11])[0]

    frame_len = len(response)

    # Output similar to reference utility
    print(f"device: {device_id:3} - events: {event_count:3}   flag: {flag:1}   event data len: {event_data_len:03}   frame len: {frame_len:03}")
    print(f"Event type: {event_type:3}   id: {event_payload:5} [0000]   payload: {event_payload:10}   device {device_id}")

def request_events(serial_port, min_slave_id, max_data_length, slave_id, flag, debug=False):
    """
    Request events from the Modbus device using the "Fast Modbus" protocol with specified parameters.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        min_slave_id (int): The minimum slave ID from which to start responding.
        max_data_length (int): The maximum length of the event data field.
        slave_id (int): The slave ID of the device from which the previous packet was received.
        flag (int): The flag confirming the previous packet received.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        bytes: The received events data, or None if an error occurred.
    """
    # Command structure: FD 46 10 <min_slave_id> <max_data_length> <slave_id> <flag>
    request_command = struct.pack('>BBBBBBB', 0xFD, 0x46, 0x10, min_slave_id, max_data_length, slave_id, flag)
    send_command(serial_port, request_command, debug)

    if wait_for_response(serial_port):
        response = serial_port.read(256)
        if debug:
            print(f"RCV (raw): {format_bytes(response)}")

        # Strip leading 0xFF bytes from the response
        response = response.lstrip(b'\xFF')

        if debug:
            print(f"RCV (filtered): {format_bytes(response)}")

        if not check_crc(response):
            print("[error] Invalid CRC in response.")
            return None
        return response
    return None

def auto_int(value):
    """
    Automatically convert a string to an integer, supporting both decimal and hex formats.

    Args:
        value (str): The string representation of the number.

    Returns:
        int: The integer value.
    """
    return int(value, 0)

def main():
    """
    Main function to parse arguments and request events from the Modbus devices as per the protocol.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Fast Modbus Event Reader with full event request support")
    parser.add_argument('-d', '--device', required=True, help="TTY serial device (e.g., /dev/ttyUSB0)")
    parser.add_argument('-b', '--baud', type=int, default=9600, help="Baudrate, default 9600")
    parser.add_argument('--min_slave_id', type=auto_int, default=1, help="Minimum slave ID to start responding. Default is 1.")
    parser.add_argument('--max_data_length', type=auto_int, default=100, help="Maximum length of event data (default 100 bytes)")
    parser.add_argument('--slave_id', type=auto_int, default=0x00, help="The slave ID from which the last event packet was received.")
    parser.add_argument('--flag', type=auto_int, default=0x00, help="Flag confirming the previous packet received.")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    args = parser.parse_args()

    serial_port = init_serial(args.device, args.baud)

    # Request events from the Modbus device with all required parameters
    result = request_events(serial_port, args.min_slave_id, args.max_data_length, args.slave_id, args.flag, debug=args.debug)
    if result:
        parse_event_response(result, debug=args.debug)
    else:
        print("Failed to read events.")

    serial_port.close()


if __name__ == "__main__":
    main()
