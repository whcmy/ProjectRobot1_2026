# -*- coding: utf-8 -*-
"""
Robot Direction Control — Compass & Serial Direction Movement
==============================================================
Receives direction commands from K210 serial or uses
micro:bit compass to navigate in 8 cardinal directions.

Protocol (from K210): $05<direction>,#
  direction = N / NE / E / SE / S / SW / W / NW / STOP

Also accepts: $20+LxxxRxxx,#  for direct motor control

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, compass
import tinybit

# --- Configuration ---
BAUDRATE = 115200
BASE_SPEED = 80

# Compass heading → direction
COMPASS_HEADINGS = {
    (0, 22): "N", (23, 67): "NE", (68, 112): "E", (113, 157): "SE",
    (158, 202): "S", (203, 247): "SW", (248, 292): "W", (293, 337): "NW",
    (338, 360): "N",
}

# Direction → wheel speeds (L, R)
DIRECTION_SPEEDS = {
    "N":  (BASE_SPEED, BASE_SPEED),
    "NE": (BASE_SPEED, BASE_SPEED // 2),
    "E":  (BASE_SPEED, -BASE_SPEED),
    "SE": (-BASE_SPEED // 2, -BASE_SPEED),
    "S":  (-BASE_SPEED, -BASE_SPEED),
    "SW": (-BASE_SPEED, -BASE_SPEED // 2),
    "W":  (-BASE_SPEED, BASE_SPEED),
    "NW": (BASE_SPEED // 2, BASE_SPEED),
}

# Direction → display icon
DIRECTION_ICONS = {
    "N": Image.ARROW_N, "NE": Image.ARROW_NE, "E": Image.ARROW_E,
    "SE": Image.ARROW_SE, "S": Image.ARROW_S, "SW": Image.ARROW_SW,
    "W": Image.ARROW_W, "NW": Image.ARROW_NW,
}

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helper: parse $20 motor command ---
def parse_motor(payload):
    """Parse $20+LxxxRxxx,# → (left_speed, right_speed)"""
    try:
        payload = payload.strip().rstrip(',')
        if len(payload) >= 8:
            left_str = payload[0:4]   # e.g. "+050" or "-030"
            right_str = payload[4:8]  # e.g. "+050" or "-030"
            left = int(left_str)
            right = int(right_str)
            return left, right
    except (ValueError, IndexError):
        pass
    return None

# --- Helper: parse $05 direction command ---
def parse_direction(payload):
    """Parse $05<direction>,# → direction string"""
    try:
        direction = payload.strip().rstrip(',').upper()
        if direction in DIRECTION_SPEEDS:
            return direction
    except Exception:
        pass
    return None

# --- Helper: read UART buffer ---
def read_uart():
    buf = ""
    while uart.any():
        b = uart.read(1)
        if b:
            ch = chr(b[0])
            if ch == '$':
                buf = '$'
            elif buf.startswith('$'):
                buf += ch
                if ch == '#':
                    return buf
    return None

# --- Main loop ---
display.show(Image.ARROW_N)

current_mode = "serial"  # "serial" or "compass"

while True:
    # --- Toggle mode with button A ---
    if button_a.was_pressed():
        current_mode = "compass" if current_mode == "serial" else "serial"

    # --- Mode: Serial control (receive from K210) ---
    if current_mode == "serial":
        cmd = read_uart()
        if cmd:
            if cmd.startswith("$20"):
                speeds = parse_motor(cmd[3:])
                if speeds:
                    left, right = speeds
                    tinybit.car_run(left, right)
                    if left > 0 and right > 0:
                        display.show(Image.ARROW_N)
                    elif left < 0 and right < 0:
                        display.show(Image.ARROW_S)
                    elif left < 0:
                        display.show(Image.ARROW_W)
                    elif right < 0:
                        display.show(Image.ARROW_E)
                    else:
                        display.show(Image.NO)

            elif cmd.startswith("$05"):
                direction = parse_direction(cmd[3:])
                if direction:
                    left, right = DIRECTION_SPEEDS[direction]
                    tinybit.car_run(left, right)
                    display.show(DIRECTION_ICONS.get(direction, Image.HAPPY))

            elif cmd == "$#":
                tinybit.car_run(0, 0)
                display.show(Image.NO)

    # --- Mode: Compass control (heading-based) ---
    else:
        heading = compass.heading()
        if heading is not None:
            direction = "N"
            for (lo, hi), d in COMPASS_HEADINGS.items():
                if lo <= heading <= hi:
                    direction = d
                    break
            left, right = DIRECTION_SPEEDS[direction]
            tinybit.car_run(left, right)
            display.show(DIRECTION_ICONS.get(direction, Image.HAPPY))

    sleep(20)
