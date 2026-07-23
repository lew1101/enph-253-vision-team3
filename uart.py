import struct

PACKET_MAGIC = 0xA55A
CRC16_INITIAL = 0xFFFF
CRC16_POLYNOMIAL = 0x1021


def crc16_ccitt(data):
    crc = CRC16_INITIAL
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ CRC16_POLYNOMIAL) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


class UartLink:
    """Python sender compatible with lib/comms UartLink packet framing."""

    def __init__(self, port):
        self._port = port
        self._packet_sequence = 0

    def send(self, payload):
        header = struct.pack("<HHH", PACKET_MAGIC, self._packet_sequence, len(payload))
        packet_without_crc = header + payload
        packet = packet_without_crc + struct.pack("<H", crc16_ccitt(packet_without_crc))

        written = self._port.write(packet)
        if written != len(packet):
            raise RuntimeError("camera UART write failed")

        self._packet_sequence = (self._packet_sequence + 1) & 0xFFFF
