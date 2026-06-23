#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Line Following — Colour-Based Path Tracking
===================================================
Implements line-following behaviour using PID-controlled
differential steering.

Features:
  - PID line-following
  - Adjustable following speed
  - Lost-line recovery behaviour
  - Junction detection
  - Simulation mode
  - Keyboard test mode

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, PID, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class LineFollower:
    """PID-based line follower."""

    IMG_CENTER_X = 160

    def __init__(self, motion, follow_speed=27, P=30, I=0, D=2):
        self.motion = motion
        self.follow_speed = follow_speed
        self.pid = PID(target=self.IMG_CENTER_X, P=P, I=I, D=D, scale=100.0)
        self.line_position = self.IMG_CENTER_X
        self.line_found = False
        self.lost_frames = 0
        self.max_lost_frames = 50

    def update(self, line_x):
        if line_x is not None:
            self.line_position = line_x
            self.line_found = True
            self.lost_frames = 0
            correction = self.pid.incremental(line_x, limit=50)
            left = int(self.follow_speed + correction)
            right = int(self.follow_speed - correction)
            left = max(-150, min(150, left))
            right = max(-150, min(150, right))
            return left, right
        else:
            self.lost_frames += 1
            if self.lost_frames > self.max_lost_frames:
                self.line_found = False
                self.pid.reset()
            return 0, 0

    def stop(self):
        self.motion.stop()

    def print_status(self):
        status = "ON LINE" if self.line_found else "LOST"
        err = self.line_position - self.IMG_CENTER_X
        print(f"\r[LINE] {status}  pos={self.line_position:3d}  "
              f"err={err:+3d}  speed={self.follow_speed:2d}  ",
              end='', flush=True)


def run_simulation_demo(motion, duration=20):
    print_banner("Simulated Line Following Demo")
    print("A virtual line meanders — watch the PID controller follow it.\n")
    follower = LineFollower(motion, follow_speed=40, P=30, I=0, D=2)
    sim_time = 0.0
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            sim_time += 0.05
            line_x = 160 + int(60 * math.sin(sim_time * 0.5) + 15 * math.sin(sim_time * 1.3))
            left, right = follower.update(line_x)
            motion.set_wheel_speeds(left, right)
            err = line_x - 160
            print(f"\r  Line X={line_x:3d} Error={err:+3d}  "
                  f"Motors: L={left:+4d} R={right:+4d}  ", end='', flush=True)
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        motion.stop()
        print("\n[STOP] Simulation ended.")


def run_keyboard_test(motion):
    print_banner("Keyboard Line Following Test")
    print("  A — move line LEFT (robot turns left)")
    print("  D — move line RIGHT (robot turns right)")
    print("  S — centre the line")
    print("  Q — quit\n")
    follower = LineFollower(motion, follow_speed=40, P=22, I=0, D=2)
    line_x = 160
    try:
        import msvcrt
        print("[READY] Use A/D to simulate line position. Q to quit.\n")
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if key == 'a':
                    line_x = max(0, line_x - 20)
                elif key == 'd':
                    line_x = min(320, line_x + 20)
                elif key == 's':
                    line_x = 160
                elif key == 'q':
                    break
            left, right = follower.update(line_x)
            motion.set_wheel_speeds(left, right)
            if line_x > 160:
                line_x -= 1
            elif line_x < 160:
                line_x += 1
            follower.print_status()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        motion.stop()
        print("\n[STOP] Test ended.")


def main():
    print_banner("Robot Line Following — Colour-Based Path Tracking")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    menu_options = [
        ('1', 'Simulation demo (sinusoidal line)'),
        ('2', 'Keyboard test (A/D to move line)'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Line Following — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion, duration=20)
        elif choice == '2':
            run_keyboard_test(motion)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Line following ended.")


if __name__ == "__main__":
    main()
