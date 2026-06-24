# -*- coding: utf-8 -*-
"""
Robot Face Recognition Control — Identity-Based Actions
=========================================================
Receives face recognition results from K210 and executes
identity-specific robot behaviors.

Works with K210 source: 2.8_face_recog.py

Protocol (from K210): $08<YN><index>,#
  Y = recognized, N = not recognized
  index = registered face index (00-99)

Behaviors:
  Recognized Face 0 → Greet (forward + backward)
  Recognized Face 1 → Follow (forward)
  Recognized Face 2 → Dance (wiggle)
  Recognized Face 3 → Circle (arc)
  Unrecognized      → Stop & wait

Button A: register current face (send signal to K210)
Button B: show last recognized ID

Hardware: micro:bit + Tinybit smart car + K210
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 80

# Face index → (behavior, speed)
FACE_BEHAVIORS = {
    0: ("greet", DEFAULT_SPEED),
    1: ("follow", DEFAULT_SPEED),
    2: ("dance", DEFAULT_SPEED),
    3: ("circle", DEFAULT_SPEED),
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

def execute_face_behavior(recognized, face_index):
    """Execute robot behavior based on face recognition result."""
    if recognized and face_index in FACE_BEHAVIORS:
        behavior, speed = FACE_BEHAVIORS[face_index]

        if behavior == "greet":
            tinybit.car_run(speed, speed)
            sleep(500)
            tinybit.car_run(-speed, -speed)
            sleep(500)
            tinybit.car_run(0, 0)

        elif behavior == "follow":
            tinybit.car_run(speed, speed)
            sleep(2000)

        elif behavior == "dance":
            for _ in range(3):
                tinybit.car_run(-speed, speed)
                sleep(300)
                tinybit.car_run(speed, -speed)
                sleep(300)
            tinybit.car_run(0, 0)

        elif behavior == "circle":
            for _ in range(25):
                tinybit.car_run(speed, speed // 3)
                sleep(150)
            tinybit.car_run(0, 0)

    elif recognized:
        # Recognized but no specific behavior — just acknowledge
        tinybit.car_run(0, 0)
        display.show(Image.YES)
    else:
        # Not recognized
        tinybit.car_run(0, 0)
        display.show(Image.SAD)


# --- Main loop ---
display.show(Image.GHOST)
last_face_index = None
running = True

while True:
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.GHOST)

    if button_b.was_pressed():
        if last_face_index is not None:
            display.scroll("F" + str(last_face_index))
        else:
            display.scroll("?")

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "08":
        # Face recognition result
        try:
            ps = payload.strip().rstrip(',')
            recognized = ps.startswith("Y")
            if recognized and len(ps) > 1:
                face_index = int(ps[1:])
            else:
                face_index = None

            last_face_index = face_index
            execute_face_behavior(recognized, face_index)

        except (ValueError, IndexError):
            pass

    elif cmd == "20":
        # Motor speed command (if in follow mode)
        try:
            p = payload.strip().rstrip(',')
            if len(p) >= 8:
                tinybit.car_run(int(p[0:4]), int(p[4:8]))
        except (ValueError, IndexError):
            pass

    elif cmd == "#":
        tinybit.car_run(0, 0)

    sleep(20)
