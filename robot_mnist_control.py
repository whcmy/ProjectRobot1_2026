# -*- coding: utf-8 -*-
"""
Robot MNIST Control — Handwritten Digit Command Interface
===========================================================
Receives MNIST digit recognition results from K210 and
executes corresponding robot commands.

Works with K210 source: 2.9_3.8_mnist.py

Protocol (from K210): $11<digit>,#
  digit = 0-9

Digit → Command mapping:
  0 — Stop            5 — Stop
  1 — Forward Slow    6 — Turn Right
  2 — Forward Medium  7 — Backward
  3 — Forward Fast    8 — Dance
  4 — Turn Left       9 — Autonomous (PATROL)

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200

# Digit → (action, speed, duration_ms)
DIGIT_COMMANDS = {
    0: ("stop", 0, 1000),
    1: ("forward", 40, 1500),
    2: ("forward", 80, 1500),
    3: ("forward", 120, 1500),
    4: ("turn_left", 60, 600),
    5: ("stop", 0, 1000),
    6: ("turn_right", 60, 600),
    7: ("backward", 60, 1500),
    8: ("dance", 80, 3000),
    9: ("patrol", 80, 5000),
}

# Digit → LED pattern
DIGIT_IMAGES = {
    0: Image("00900:09090:09090:09090:00900"),
    1: Image("00900:09900:00900:00900:09990"),
    2: Image("09990:00090:09990:09000:09990"),
    3: Image("09990:00090:09990:00090:09990"),
    4: Image("09090:09090:09990:00090:00090"),
    5: Image("09990:09000:09990:00090:09990"),
    6: Image("09990:09000:09990:09090:09990"),
    7: Image("09990:00090:00090:00090:00090"),
    8: Image("09990:09090:09990:09090:09990"),
    9: Image("09990:09090:09990:00090:09990"),
}

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

def execute_digit(digit):
    """Execute robot action for a recognized digit."""
    if digit not in DIGIT_COMMANDS:
        return

    action, speed, duration = DIGIT_COMMANDS[digit]

    # Show digit on LED
    if digit in DIGIT_IMAGES:
        display.show(DIGIT_IMAGES[digit])

    # Execute action
    if action == "stop":
        tinybit.car_run(0, 0)
    elif action == "forward":
        tinybit.car_run(speed, speed)
    elif action == "backward":
        tinybit.car_run(-speed, -speed)
    elif action == "turn_left":
        tinybit.car_run(-speed, speed)
    elif action == "turn_right":
        tinybit.car_run(speed, -speed)
    elif action == "dance":
        # Wiggle dance
        for _ in range(3):
            tinybit.car_run(-speed, speed)
            sleep(300)
            tinybit.car_run(speed, -speed)
            sleep(300)
        tinybit.car_run(0, 0)
    elif action == "patrol":
        # Autonomous patrol: forward + occasional turns
        for _ in range(3):
            tinybit.car_run(speed, speed)
            sleep(1000)
            tinybit.car_run(speed, -speed)
            sleep(350)
        tinybit.car_run(0, 0)

    # Hold for duration then stop
    sleep(duration)
    tinybit.car_run(0, 0)

# --- Main loop ---
display.show(Image.HAPPY)
last_digit = None
running = True

while True:
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.HAPPY)

    if button_b.was_pressed() and last_digit is not None:
        display.scroll(str(last_digit))

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "11":
        try:
            digit = int(payload.strip().rstrip(','))
            if 0 <= digit <= 9:
                last_digit = digit
                execute_digit(digit)
        except ValueError:
            pass

    sleep(20)
