import argparse
import struct
import serial
import time

# CRC16 calculation
def calculate_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

# Function to send command to the device
def send_command(serial_port, command, debug=False):
    crc = calculate_crc(command)
    command += struct.pack('<H', crc)
    if debug:
        print(f"[debug] Command generated: {' '.join(f'0x{byte:02X}' for byte in command)}")
    serial_port.write(command)

# Initialize serial port
def init_serial(device, baudrate):
    return serial.Serial(port=device, baudrate=baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

# Formulate the event configuration command for multiple register ranges
def formulate_command(slave_id, config, debug=False):
    command = [slave_id, 0x46, 0x18]  # Start with slave id, command, sub-command
    data = []

    for cfg in config.split(','):
        reg_type, address, count, priority = cfg.split(':')
        address, count, priority = int(address), int(count), int(priority)

        # Assign type byte based on register type
        reg_type_byte = {
            "coil": 0x01,
            "discrete": 0x02,
            "holding": 0x03,
            "input": 0x04
        }.get(reg_type.lower())

        if reg_type_byte is None:
            raise ValueError(f"Unknown register type: {reg_type}")

        # Adding the register type, address (big endian), count (in u16)
        data.append(reg_type_byte)
        data += list(struct.pack('>H', address))  # Address in big endian
        data.append(count)  # Count of u16 registers
        data += [priority] * count  # Priority for each u16 register

        if debug:
            print(f"[debug] Range: {reg_type} Address: {address} Count: {count} Priority: {priority}")

    # Length of data
    command.append(len(data))
    command += data
    return command

# Parse the response from the device
def parse_response(response, debug=False):
    response = response.lstrip(b'\xFF')
    if debug:
        print(f"RAW Response (before filtering): {response}")
    if len(response) < 4:
        print("[error] Response too short to be valid")
        return None

    slave_id, command, sub_command, length = response[:4]
    mask_data = response[4:4+length]
    return mask_data

# Print human-readable register settings
def print_settings(config, mask_data, slave_id):
    byte_index = 0
    print(f"Device: {slave_id}")
    for cfg in config.split(','):
        reg_type, address, count, _ = cfg.split(':')
        address, count = int(address), int(count)

        print(f"Settings for {reg_type.capitalize()} registers:")
        for i in range(count):
            if byte_index < len(mask_data):
                mask_byte = mask_data[byte_index]
                bit_position = i % 8
                bit = (mask_byte >> bit_position) & 1
                reg_address = address + i
                status = "enabled" if bit else "disabled"
                print(f"- Register {reg_address} (u16): {status}")

            if (i + 1) % 8 == 0:
                byte_index += 1

# Configure events for multiple register ranges
def configure_events(serial_port, slave_id, config, debug=False):
    for cfg in config.split(','):
        command = formulate_command(slave_id, cfg, debug)
        send_command(serial_port, command, debug)

        time.sleep(1)
        response = serial_port.read(256)
        if debug:
            print(f"RAW Response: {response}")

        mask_data = parse_response(response, debug)
        if mask_data:
            print_settings(cfg, mask_data, slave_id)
        else:
            print("[error] No valid response received")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Modbus Event Configuration Tool for multiple u16 register ranges")
    parser.add_argument('--device', required=True, help="Serial device (e.g., /dev/ttyUSB0)")
    parser.add_argument('--baud', type=int, default=9600, help="Baud rate, default is 9600")
    parser.add_argument('--slave_id', type=int, required=True, help="Slave ID of the device")
    parser.add_argument('--config', required=True, help="Configuration string (e.g., 'input:60:2:1,discrete:0:8:1')")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    args = parser.parse_args()

    serial_port = init_serial(args.device, args.baud)
    configure_events(serial_port, args.slave_id, args.config, args.debug)
    serial_port.close()

if __name__ == "__main__":
    main()
