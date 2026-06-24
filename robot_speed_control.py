# -*- coding: utf-8 -*-
"""
Robot Speed Control — Motor Speed Calibration & Demo
======================================================
Speed ramp and calibration utility for the Tinybit car.
Cycles through different speed levels to help calibrate
motor response.

Button controls:
  Button A     — Cycle speed level up
  Button B     — Cycle speed level down
  Button A+B   — Run current speed for 2 seconds
  Shake        — Emergency stop

Speed levels (0-10):
  L0: Stop      L1: 25    L2: 50    L3: 75    L4: 100
  L5: 125       L6: 150   L7: 175   L8: 200   L9: 225  L10: 255

Also accepts serial motor commands: $20+LxxxRxxx,#

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b, accelerometer
import tinybit

# --- Configuration ---
BAUDRATE = 115200

# Speed levels (0-10 → motor value 0-255)
SPEED_LEVELS = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 255]

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helpers ---
def read_command():
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

def show_speed_level(level):
    """Display speed level on LED matrix (0-10)."""
    if level == 0:
        display.show(Image.NO)
        return
    # Light up rows proportional to speed
    pixels = min(level, 5)
    rows = []
    for r in range(5):
        if r >= 5 - pixels:
            rows.append("9" * 5)
        else:
            rows.append("0" * 5)
    img_str = ":".join(rows)
    display.show(Image(img_str))


# --- Main loop ---
current_level = 5  # Start at medium speed (125)
show_speed_level(current_level)

while True:
    # Check serial commands from K210
    cmd, payload = read_command()
    if cmd == "20":
        try:
            p = payload.strip().rstrip(',')
            if len(p) >= 8:
                tinybit.car_run(int(p[0:4]), int(p[4:8]))
        except (ValueError, IndexError):
            pass
        continue

    # Button A: increase speed
    if button_a.was_pressed():
        if current_level < 10:
            current_level += 1
            show_speed_level(current_level)

    # Button B: decrease speed
    if button_b.was_pressed():
        if current_level > 0:
            current_level -= 1
            show_speed_level(current_level)

    # Button A+B held: run at current speed
    if button_a.is_pressed() and button_b.is_pressed():
        speed = SPEED_LEVELS[current_level]
        tinybit.car_run(speed, speed)
        sleep(2000)
        tinybit.car_run(0, 0)

    # Shake: emergency stop
    if accelerometer.was_gesture("shake"):
        tinybit.car_run(0, 0)
        display.show(Image.SKULL)
        sleep(1000)
        show_speed_level(current_level)

    sleep(50)
