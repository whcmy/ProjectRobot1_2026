# -*- coding: utf-8 -*-
"""
Robot Line Following — PID-Controlled Line Tracking
=====================================================
Receives line position data from K210 via serial and follows
the line using incremental PID control.

Protocol (from K210): $20+LxxxRxxx,#
  The K210 computes motor speeds via PID and sends directly.
  micro:bit passes them to tinybit motors.

  L / R: signed 3-digit speed values  (-255 ~ 255)
  Positive = forward, Negative = backward

When used with K210 source code 3.9_color_follow_line.py,
the K210 handles all vision and PID computation, and the
micro:bit simply executes the received motor commands.

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helper: parse $20 motor speed command ---
def parse_motor(payload):
    """
    Parse $20+LxxxRxxx,#  payload.
    Returns (left, right) signed speeds, or None on error.
    """
    try:
        payload = payload.strip().rstrip(',')
        if len(payload) >= 8:
            left = int(payload[0:4])
            right = int(payload[4:8])
            return left, right
    except (ValueError, IndexError):
        pass
    return None

# --- Helper: read and parse a full protocol packet from UART ---
def read_command():
    """Read UART buffer and return (cmd_code, payload) or (None, None)."""
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
                # Parse: $ + cmd_code(2 chars) + payload + , + #
                inner = buf[1:]  # remove '$'
                if len(inner) >= 2:
                    cmd = inner[0:2]
                    payload = inner[2:]
                    return cmd, payload
                return None, None
            else:
                buf += ch
    return None, None

# --- Main loop ---
display.show(Image.ARROW_S)  # S for "Start line following"

running = True
last_left = 0
last_right = 0

while True:
    # Button A: toggle run/stop
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.ARROW_S)

    # Button B: emergency stop
    if button_b.was_pressed():
        tinybit.car_run(0, 0)
        running = False
        display.show(Image.SKULL)

    if not running:
        sleep(50)
        continue

    # Read serial commands from K210
    cmd, payload = read_command()

    if cmd == "20":
        # Motor speed command from K210 line-following PID
        speeds = parse_motor(payload)
        if speeds:
            left, right = speeds
            tinybit.car_run(left, right)
            last_left, last_right = left, right
            # Show direction on LED
            if left > 0 and right > 0:
                display.show(Image.ARROW_N)
            elif left < 0 and right < 0:
                display.show(Image.ARROW_S)
            elif abs(left) < 5 and abs(right) < 5:
                display.show(Image.HAPPY)
            else:
                display.show(Image.ARROW_E if right < left else Image.ARROW_W)

    elif cmd and not cmd.startswith("#"):
        # Other vision data — keep current motor state
        pass

    elif cmd == "#" or (cmd is None and payload is None and uart.any() == 0):
        # Stop signal or idle
        pass

    sleep(10)
