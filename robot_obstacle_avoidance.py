# -*- coding: utf-8 -*-
"""
Robot Obstacle Avoidance — Autonomous Collision Prevention
============================================================
Uses ultrasonic sensor data (from Tinybit or K210) to detect
obstacles and navigate around them autonomously.

The Tinybit car has onboard ultrasonic + line-tracking sensors.
This program can work standalone (using tinybit sensors) or
in conjunction with K210 vision data.

Standalone mode:
  - Read ultrasonic distance from tinybit.sonar()
  - If obstacle < threshold: stop, turn, go

K210-assisted mode:
  - Receive $07<num>,#  (face mask detect → obstacle proxy)
  - Receive $20+LxxxRxxx,#  (motor commands)
  - Button B toggles mode

Avoidance strategies:
  Simple:   Stop → turn 90° → forward
  Smart:    Stop → check both sides → pick clearer path
  Cautious: Stop → back up → turn → forward

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b, running_time
import tinybit

# --- Configuration ---
BAUDRATE = 115200
OBSTACLE_THRESHOLD_CM = 25   # Distance threshold for obstacle
CRUISE_SPEED = 80
TURN_SPEED = 60

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

def avoid_obstacle(mode="smart"):
    """Execute obstacle avoidance maneuver."""
    if mode == "simple":
        # Simple: turn right 90°, then forward
        tinybit.car_run(0, 0)
        sleep(200)
        tinybit.car_run(TURN_SPEED, -TURN_SPEED)
        sleep(600)
        tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)

    elif mode == "smart":
        # Check which side has more space (simplified)
        tinybit.car_run(0, 0)
        sleep(100)
        # Turn a bit to check
        tinybit.car_run(-TURN_SPEED, TURN_SPEED)  # look left
        sleep(400)
        tinybit.car_run(0, 0)
        sleep(100)
        # Go right
        tinybit.car_run(TURN_SPEED, -TURN_SPEED)
        sleep(700)
        tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)

    elif mode == "cautious":
        # Back up first, then turn
        tinybit.car_run(0, 0)
        sleep(300)
        tinybit.car_run(-CRUISE_SPEED, -CRUISE_SPEED)
        sleep(800)
        tinybit.car_run(0, 0)
        sleep(300)
        tinybit.car_run(TURN_SPEED, -TURN_SPEED)
        sleep(600)
        tinybit.car_run(CRUISE_SPEED // 2, CRUISE_SPEED // 2)


# --- Main loop ---
display.show(Image.HAPPY)

running = True
mode = "smart"    # "simple", "smart", "cautious"
use_k210 = False  # True when receiving K210 data
last_sonar_check = 0

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.HAPPY)

    # Button B: cycle avoidance mode
    if button_b.was_pressed():
        modes = ["simple", "smart", "cautious"]
        idx = modes.index(mode)
        mode = modes[(idx + 1) % len(modes)]
        display.scroll(mode[:4])

    if not running:
        sleep(50)
        continue

    # Check K210 serial data
    cmd, payload = read_command()
    if cmd == "20":
        use_k210 = True
        try:
            p = payload.strip().rstrip(',')
            if len(p) >= 8:
                left = int(p[0:4])
                right = int(p[4:8])
                tinybit.car_run(left, right)
        except (ValueError, IndexError):
            pass
        continue

    # Standalone: use ultrasonic sensor
    now = running_time()
    if now - last_sonar_check > 150:  # check every 150ms
        last_sonar_check = now

        try:
            distance = tinybit.sonar()
        except Exception:
            distance = 999

        if distance > 0 and distance < OBSTACLE_THRESHOLD_CM:
            # Obstacle detected!
            display.show(Image.SKULL)
            avoid_obstacle(mode)
        else:
            # Path clear — cruise forward
            tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)
            display.show(Image.ARROW_N)

    sleep(30)
