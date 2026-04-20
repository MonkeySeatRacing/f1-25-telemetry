"""
UDP listener for F1 25 telemetry packets.
"""

import socket
from typing import Optional

from f1_25_telemetry.packets import PacketHeader, HEADER_FIELD_TO_PACKET_TYPE


class TelemetryListener:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        if not port:
            port = 20777

        if not host:
            host = '0.0.0.0'

        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind((host, port))

    def get(self):
        packet = self.socket.recv(4096)
        header = PacketHeader.from_buffer_copy(packet)

        key = (header.packet_format, header.packet_version, header.packet_id)

        if key not in HEADER_FIELD_TO_PACKET_TYPE:
            raise ValueError(
                f'Unknown packet type: format={header.packet_format}, '
                f'version={header.packet_version}, id={header.packet_id}'
            )

        return HEADER_FIELD_TO_PACKET_TYPE[key].unpack(packet)
