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

def read_registers(serial_port, serial_number, command, register, count=1, debug=False):
    """
    Read Modbus registers from the device.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        serial_number (int): The serial number of the device.
        command (int): The Modbus command (e.g., 0x03 for read).
        register (int): The starting register address.
        count (int, optional): The number of registers to read. Defaults to 1.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        bytes: The data read from the registers, or None if an error occurred.
    """
    request_command = struct.pack('>BBBIBHH', 0xFD, 0x46, 0x08, serial_number, command, register, count)
    send_command(serial_port, request_command, debug)

    if wait_for_response(serial_port):
        response = serial_port.read(256)
        if debug:
            print(f"RCV: {format_bytes(response)}")
        if not check_crc(response) or len(response) < 9 + 2 * count:
            print("[error] Invalid or short response.")
            return None
        return response[9:9 + 2 * count]
    return None

def write_registers(serial_port, serial_number, command, register, values, debug=False):
    """
    Write values to Modbus registers on the device.

    Args:
        serial_port (serial.Serial): The initialized serial port object.
        serial_number (int): The serial number of the device.
        command (int): The Modbus command (e.g., 0x10 for write).
        register (int): The starting register address.
        values (list of int): The values to write to the registers.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        bool: True if the write was successful, False otherwise.
    """
    register_count = len(values)
    write_command = struct.pack('>BBBIBHHB', 0xFD, 0x46, 0x08, serial_number, command, register, register_count, register_count * 2)
    write_command += struct.pack(f'>{register_count}H', *values)
    send_command(serial_port, write_command, debug)

    if wait_for_response(serial_port):
        response = serial_port.read(256)
        if debug:
            print(f"RCV: {format_bytes(response)}")
        return check_crc(response)
    return False

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
    Main function to parse arguments and perform Modbus register operations (read/write).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Fast Modbus Client Tool")
    parser.add_argument('-d', '--device', required=True, help="TTY serial device (e.g., /dev/ttyUSB0)")
    parser.add_argument('-b', '--baud', type=int, default=9600, help="Baudrate, default 9600")
    parser.add_argument('-s', '--serial', type=auto_int, required=True, help="Device serial number (decimal or hex)")
    parser.add_argument('-c', '--command', type=auto_int, required=True, help="Modbus command (decimal or hex)")
    parser.add_argument('-r', '--register', type=auto_int, required=True, help="Register to read/write (decimal or hex)")
    parser.add_argument('-n', '--count', type=auto_int, default=1, help="Number of registers to read (default 1)")
    parser.add_argument('-w', '--write', nargs='*', type=auto_int, help="Values to write (if write operation, decimal or hex)")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    parser.add_argument('--decimal-output', action='store_true', help="Display register values in decimal format")
    args = parser.parse_args()

    serial_port = init_serial(args.device, args.baud)

    if args.write:
        success = write_registers(serial_port, args.serial, args.command, args.register, args.write, debug=args.debug)
        print(f"Successfully wrote {len(args.write)} registers." if success else "Failed to write registers.")
    else:
        result = read_registers(serial_port, args.serial, args.command, args.register, args.count, debug=args.debug)
        if result:
            if args.decimal_output:
                registers = ' '.join(str(int.from_bytes(result[i:i + 2], byteorder='big')) for i in range(0, len(result), 2))
            else:
                registers = ' '.join(f"0x{int.from_bytes(result[i:i + 2], byteorder='big'):04X}" for i in range(0, len(result), 2))
            print(f"Read {args.count} registers from device {args.serial}: {registers}")
        else:
            print("Failed to read registers.")

    serial_port.close()

if __name__ == "__main__":
    main()
