# -*- coding: utf-8 -*-
"""
Robot Color Tracking — Follow Colored Objects
===============================================
Receives color detection data from K210 via serial and
follows the detected color target.

Works with K210 source: 3.1_color_rgb.py or 3.11_follow_color.py

Protocol (from K210):
  $01<R/G/B/Y>,#           — Color detected (RGB LED feedback)
  $20+LxxxRxxx,#            — Motor speed command (from follow_color K210)

Behavior:
  - R (Red)    → LED: show red pattern, follow
  - G (Green)  → LED: show green pattern, follow
  - B (Blue)   → LED: show blue pattern, follow
  - Y (Yellow) → LED: show yellow pattern, follow
  - No color   → stop

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a
import tinybit

# --- Configuration ---
BAUDRATE = 115200

# --- Custom LED images for each color ---
IMG_RED = Image("00000:00000:00900:00000:00000")
IMG_GREEN = Image("00000:00000:09000:00000:00000")
IMG_BLUE = Image("00000:00000:90000:00000:00000")
IMG_YELLOW = Image("09090:90009:00000:90009:09090")

COLOR_ICONS = {
    "R": IMG_RED,
    "G": IMG_GREEN,
    "B": IMG_BLUE,
    "Y": IMG_YELLOW,
}

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

def parse_color(payload):
    """Parse $01<color>,# → color char or None."""
    try:
        c = payload.strip().rstrip(',').upper()
        if c in ("R", "G", "B", "Y"):
            return c
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
display.show(Image.HAPPY)

current_color = None
running = True

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "20":
        # Motor speed command (from color-following K210)
        speeds = parse_motor(payload)
        if speeds:
            tinybit.car_run(speeds[0], speeds[1])

    elif cmd == "01":
        # Color detected — show on LED
        color = parse_color(payload)
        if color and color != current_color:
            current_color = color
            display.show(COLOR_ICONS.get(color, Image.HAPPY))

    elif cmd is not None and cmd != "01" and cmd != "20":
        pass  # ignore other commands

    sleep(10)
