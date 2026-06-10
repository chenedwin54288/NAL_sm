"""Shared framing for timestamped client/server probe records.

The probe transport is TCP, so these are application-level probe records inside
the byte stream. Timestamp fields on the wire are unsigned integer nanoseconds
since the Unix epoch according to the sending host clock.
"""

from __future__ import annotations

import struct
import time


PROBE_MAGIC = b"PB01"
FRAME_TYPE_PROBE = 1
FRAME_TYPE_STOP = 2

# magic, frame_type, padding, seq, send_timestamp_ns, payload_size
PROBE_HEADER = struct.Struct("!4sB3xQQI")
PROBE_HEADER_SIZE = PROBE_HEADER.size


def pack_probe_header(seq: int, send_timestamp_ns: int, payload_size: int) -> bytes:
    validate_uint64(seq, "seq")
    validate_uint64(send_timestamp_ns, "send_timestamp_ns")
    validate_uint32(payload_size, "payload_size")
    return PROBE_HEADER.pack(
        PROBE_MAGIC,
        FRAME_TYPE_PROBE,
        seq,
        send_timestamp_ns,
        payload_size,
    )


def pack_stop_header(seq: int, send_timestamp_ns: int | None = None) -> bytes:
    validate_uint64(seq, "seq")
    if send_timestamp_ns is None:
        send_timestamp_ns = time.time_ns()
    validate_uint64(send_timestamp_ns, "send_timestamp_ns")
    return PROBE_HEADER.pack(
        PROBE_MAGIC,
        FRAME_TYPE_STOP,
        seq,
        send_timestamp_ns,
        0,
    )


def unpack_header(header: bytes) -> tuple[int, int, int, int]:
    if len(header) != PROBE_HEADER_SIZE:
        raise ValueError(
            f"probe header must be {PROBE_HEADER_SIZE} bytes, got {len(header)}"
        )

    magic, frame_type, seq, send_timestamp_ns, payload_size = PROBE_HEADER.unpack(
        header
    )
    if magic != PROBE_MAGIC:
        raise ValueError("invalid probe frame magic")
    if frame_type not in (FRAME_TYPE_PROBE, FRAME_TYPE_STOP):
        raise ValueError(f"unsupported probe frame type: {frame_type}")
    if frame_type == FRAME_TYPE_STOP and payload_size != 0:
        raise ValueError("stop probe frame must not carry payload")

    return frame_type, seq, send_timestamp_ns, payload_size


def validate_uint64(value: int, name: str) -> None:
    if value < 0 or value > 0xFFFFFFFFFFFFFFFF:
        raise ValueError(f"{name} must fit in uint64")


def validate_uint32(value: int, name: str) -> None:
    if value < 0 or value > 0xFFFFFFFF:
        raise ValueError(f"{name} must fit in uint32")
