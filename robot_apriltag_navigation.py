# -*- coding: utf-8 -*-
"""
Robot AprilTag Navigation — Fiducial Marker Following
=======================================================
Receives AprilTag detection data from K210 and navigates
toward / follows detected AprilTag markers.

Works with K210 source: 2.4_find_apriltags.py or 3.10_follow_apriltag.py

Protocol (from K210):
  $04<id>,<family>,#  — AprilTag detected (ID + family name)
  $20+LxxxRxxx,#       — Motor speed command (from follow_apriltag K210)

When using 3.10_follow_apriltag.py (PID follow mode),
the K210 computes PID and sends $20 motor commands directly.
When using 2.4_find_apriltags.py (detection mode),
the micro:bit shows tag info on LED and waits for motor commands.

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helpers ---
def parse_motor(payload):
    """Parse $20+LxxxRxxx,# → (left, right) or None."""
    try:
        payload = payload.strip().rstrip(',')
        if len(payload) >= 8:
            return int(payload[0:4]), int(payload[4:8])
    except (ValueError, IndexError):
        pass
    return None

def parse_apriltag(payload):
    """Parse $04<id>,<family>,# → (tag_id, family) or None."""
    try:
        payload = payload.strip().rstrip(',')
        parts = payload.split(',')
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    except Exception:
        pass
    return None

def read_command():
    """Read one complete $... # packet from UART."""
    buf = ""
    while uart.any():
        b = uart.read(1)
        if b is None:
            continue
        ch = chr(b[0])
        if ch == '$':
            buf = '$'
        elif buf.startswith('$'):
            if ch == '#':
                inner = buf[1:]
                if len(inner) >= 2:
                    return inner[0:2], inner[2:]
                return None, None
            else:
                buf += ch
    return None, None

# --- Main loop ---
display.show(Image.TARGET)  # target icon placeholder

running = True
last_tag_id = None

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.TARGET)

    # Button B: show last tag ID
    if button_b.was_pressed() and last_tag_id is not None:
        display.scroll("T" + last_tag_id)

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "20":
        # Motor speed command (PID follow mode)
        speeds = parse_motor(payload)
        if speeds:
            tinybit.car_run(speeds[0], speeds[1])

    elif cmd == "04":
        # AprilTag detected
        tag_info = parse_apriltag(payload)
        if tag_info:
            tag_id, family = tag_info
            last_tag_id = tag_id
            # Show tag ID on LED (1-5 pixels based on ID)
            try:
                dots = min(int(tag_id), 25)
                rows = ["0" * 5 for _ in range(5)]
                for i in range(dots):
                    row, col = divmod(i, 5)
                    r = list(rows[row])
                    r[col] = '9'
                    rows[row] = "".join(r)
                img_str = ":".join(rows)
                display.show(Image(img_str))
            except Exception:
                display.show(Image.YES)

    elif cmd == "#":
        tinybit.car_run(0, 0)

    sleep(10)
