# -*- coding: utf-8 -*-
"""
Robot Autonomous Exploration — Curiosity-Driven Navigation
============================================================
Implements autonomous exploration behavior combining
ultrasonic obstacle avoidance and random exploration.

The robot explores its environment without human control:
  - Drives forward until it detects an obstacle
  - Turns away from obstacles using ultrasonic sensor
  - Periodically changes direction to cover more area
  - Shows exploration status on LED display

Modes (button-selectable):
  1. Random walk — Move forward, random turns on obstacles
  2. Wall follow — Follow along walls/perimeter
  3. Curiosity — Forward + periodic direction changes
  4. Combined — Switch strategies dynamically

Can also receive K210 vision data via serial:
  $09<id>,#   — Object detection (react to objects)
  $20+LxxxRxxx,# — Direct motor control overrides

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b, running_time
import tinybit
import random

# --- Configuration ---
BAUDRATE = 115200
CRUISE_SPEED = 80
TURN_SPEED = 60
OBSTACLE_THRESHOLD = 20  # cm

# --- Exploration modes ---
MODES = ["random", "wall_follow", "curiosity"]
MODE_ICONS = {
    "random": Image("90009:09090:00900:09090:90009"),
    "wall_follow": Image("09000:09000:09000:09000:09990"),
    "curiosity": Image.HEART,
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

def get_distance():
    """Read ultrasonic sensor distance (cm). Returns 999 on error."""
    try:
        dist = tinybit.sonar()
        return dist if dist > 0 else 999
    except Exception:
        return 999


def step_random():
    """Random walk step — forward unless obstacle."""
    dist = get_distance()
    if dist < OBSTACLE_THRESHOLD:
        # Obstacle: random turn direction
        if random.randint(0, 1) == 0:
            tinybit.car_run(-TURN_SPEED, TURN_SPEED)  # left
        else:
            tinybit.car_run(TURN_SPEED, -TURN_SPEED)  # right
        sleep(random.randint(400, 1000))
    else:
        tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)
    display.show(Image.ARROW_N)


def step_wall_follow():
    """Wall following step — keep wall on right side."""
    dist = get_distance()
    if dist < OBSTACLE_THRESHOLD:
        # Too close to wall/obstacle: turn left
        tinybit.car_run(-TURN_SPEED, TURN_SPEED)
        display.show(Image.ARROW_W)
        sleep(300)
    elif dist > OBSTACLE_THRESHOLD * 2:
        # Too far from wall: turn right
        tinybit.car_run(TURN_SPEED, -TURN_SPEED)
        display.show(Image.ARROW_E)
        sleep(200)
    else:
        # Follow wall
        tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)
        display.show(Image.ARROW_N)


def step_curiosity():
    """Curiosity-driven step — periodically change direction."""
    dist = get_distance()

    if dist < OBSTACLE_THRESHOLD:
        # Obstacle: avoid
        tinybit.car_run(TURN_SPEED, -TURN_SPEED)
        display.show(Image.ARROW_E)
        sleep(700)
    elif random.randint(1, 30) == 1:
        # Random direction change (~every 30 steps)
        r = random.random()
        if r < 0.3:
            tinybit.car_run(-TURN_SPEED, TURN_SPEED)
            sleep(300)
        elif r < 0.6:
            tinybit.car_run(TURN_SPEED, -TURN_SPEED)
            sleep(300)
        elif r < 0.8:
            tinybit.car_run(-CRUISE_SPEED, -CRUISE_SPEED)
            sleep(500)
        display.show(Image.SURPRISED)
        sleep(100)
    else:
        tinybit.car_run(CRUISE_SPEED, CRUISE_SPEED)


# --- Main loop ---
current_mode = "curiosity"
mode_idx = MODES.index(current_mode)
display.show(MODE_ICONS[current_mode])

running = True
step_count = 0
last_step_time = 0

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(MODE_ICONS[current_mode])

    # Button B: cycle exploration mode
    if button_b.was_pressed():
        mode_idx = (mode_idx + 1) % len(MODES)
        current_mode = MODES[mode_idx]
        display.show(MODE_ICONS[current_mode])
        sleep(500)
        display.scroll(current_mode[:6])

    if not running:
        sleep(50)
        continue

    # Check for K210 serial data (overrides autonomous behavior)
    cmd, payload = read_command()
    if cmd == "20":
        try:
            p = payload.strip().rstrip(',')
            if len(p) >= 8:
                tinybit.car_run(int(p[0:4]), int(p[4:8]))
        except (ValueError, IndexError):
            pass
        continue

    # Autonomous exploration step
    now = running_time()
    if now - last_step_time > 150:
        last_step_time = now
        step_count += 1

        if current_mode == "random":
            step_random()
        elif current_mode == "wall_follow":
            step_wall_follow()
        elif current_mode == "curiosity":
            step_curiosity()

        # Show step count on LED every 50 steps (brief blink)
        if step_count % 50 == 0 and step_count > 0:
            display.scroll(str(step_count), wait=False, loop=False)

    sleep(30)
