#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Direction Control — Multi-Direction Movement
===================================================
Implements precise directional movement control.
The robot can move at any specified angle (0-360 degrees)
and execute compound direction sequences.

Features:
  - Move at arbitrary angles (0=forward, 90=right, 180=backward, 270=left)
  - Compass-point navigation (N, NE, E, SE, S, SW, W, NW)
  - Timed directional bursts
  - Programmable direction sequences
  - Real-time keyboard direction control

Control mode:   Menu-driven + keyboard
Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class DirectionController:
    """Precise directional movement controller."""

    COMPASS = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5,
    }

    @staticmethod
    def angle_to_wheel_speeds(angle, speed, max_speed=150):
        angle = angle % 360
        rad = math.radians(angle)
        turn_factor = math.sin(rad)
        fwd_factor = math.cos(rad)
        s = abs(speed)
        fwd = s * fwd_factor
        if turn_factor >= 0:
            left = fwd + s * turn_factor
            right = fwd - s * turn_factor * 0.5
        else:
            right = fwd - s * turn_factor
            left = fwd + s * turn_factor * 0.5
        left = max(-max_speed, min(max_speed, int(left)))
        right = max(-max_speed, min(max_speed, int(right)))
        return left, right

    @staticmethod
    def compass_to_angle(direction):
        d = direction.upper()
        if d in DirectionController.COMPASS:
            return DirectionController.COMPASS[d]
        return None


class DirectionCommandHandler:
    """Handles direction-based commands and executes movement."""

    def __init__(self, motion):
        self.motion = motion
        self.dc = DirectionController()
        self.default_speed = 100
        self.default_duration = 1.0

    def move_angle(self, angle, speed=None, duration=None):
        s = speed if speed is not None else self.default_speed
        left, right = self.dc.angle_to_wheel_speeds(angle, s)
        self.motion.set_wheel_speeds(left, right)
        print(f"[DIR] angle={angle:6.1f}  ->  L={left:+4d}  R={right:+4d}")
        if duration:
            time.sleep(duration)
            self.motion.stop()

    def move_compass(self, direction, speed=None, duration=None):
        angle = self.dc.compass_to_angle(direction)
        if angle is not None:
            print(f"[DIR] {direction:>3s} ({angle:6.1f})", end='  ')
            self.move_angle(angle, speed, duration)
        else:
            print(f"[ERROR] Unknown direction: {direction}")

    def execute_sequence(self, sequence, loop=1):
        for lap in range(loop):
            print(f"\n--- Sequence lap {lap + 1}/{loop} ---")
            for i, item in enumerate(sequence):
                direction, speed, duration = item
                print(f"  Step {i+1}: ", end='')
                if isinstance(direction, str):
                    self.move_compass(direction, speed, duration)
                else:
                    self.move_angle(direction, speed, duration)
                time.sleep(0.1)
            self.motion.stop()
        print("\n[SEQ] Sequence complete.")


def interactive_direction_mode(handler):
    print("""
  +--------------------------------------------------+
  |     Interactive Direction Control Mode           |
  +--------------------------------------------------+
  |  Enter angle (0-360) or compass (N/NE/E/...)    |
  |  Format:  <angle|compass> [speed] [duration]     |
  |  Examples:  45          — move at 45 deg         |
  |             NE 120 2    — NE, speed 120, 2 sec   |
  |             stop        — stop the robot         |
  |             quit        — exit this mode         |
  +--------------------------------------------------+
""")
    while True:
        try:
            cmd = input("\nDirection> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('quit', 'exit', 'q'):
                break
            if cmd.lower() == 'stop':
                handler.motion.stop()
                print("[STOP]")
                continue
            parts = cmd.split()
            direction = parts[0]
            speed = int(parts[1]) if len(parts) > 1 else None
            duration = float(parts[2]) if len(parts) > 2 else None
            try:
                angle = float(direction)
                handler.move_angle(angle, speed, duration)
            except ValueError:
                handler.move_compass(direction, speed, duration)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
    handler.motion.stop()


def demo_compass_rose(handler, speed=100, step_time=0.8):
    print_banner("Demo — Compass Rose")
    for d in ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']:
        handler.move_compass(d, speed, step_time)
        time.sleep(0.3)
    handler.motion.stop()


def demo_star_pattern(handler, speed=100):
    print_banner("Demo — Star Pattern")
    for i in range(5):
        handler.move_angle(i * 72, speed, 1.5)
        time.sleep(0.3)
    handler.motion.stop()


def demo_360_sweep(handler, speed=80):
    print_banner("Demo — 360 Degree Sweep")
    for angle in range(0, 360, 30):
        handler.move_angle(angle, speed, 0.6)
        time.sleep(0.2)
    handler.motion.stop()


def main():
    print_banner("Robot Direction Control — Multi-Direction Movement")
    robot_serial = RobotSerial()
    if not robot_serial.is_connected():
        print("[SIM] Running in simulation mode.\n")
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    handler = DirectionCommandHandler(motion)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()

    menu_options = [
        ('1', 'Interactive direction control (type angles/compass)'),
        ('2', 'Demo — Compass Rose (8 directions)'),
        ('3', 'Demo — Star Pattern (5-point)'),
        ('4', 'Demo — 360 Degree Sweep'),
        ('5', 'Demo — Square Path (90 deg turns)'),
        ('q', 'Quit'),
    ]

    while True:
        print_menu("Direction Control — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            interactive_direction_mode(handler)
        elif choice == '2':
            demo_compass_rose(handler, speed=100, step_time=1.0)
        elif choice == '3':
            demo_star_pattern(handler, speed=100)
        elif choice == '4':
            demo_360_sweep(handler, speed=80)
        elif choice == '5':
            print_banner("Demo — Square Path")
            for _ in range(4):
                handler.move_angle(0, 120, 2.0)
                time.sleep(0.2)
                handler.move_angle(90, 100, 0.5)
                time.sleep(0.2)
            motion.stop()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    motion.stop()
    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Direction control ended.")


if __name__ == "__main__":
    main()
