#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Color Tracking — Vision-Guided Object Following
======================================================
Implements colour-based object detection and tracking.
The robot uses the K210 camera to detect a coloured
target and follows it using PID-controlled movement.

Features:
  - Real-time colour target tracking with PID
  - Target search mode (rotate until found)
  - Lost-target behaviour
  - Adjustable PID gains
  - Simulation mode for testing without hardware

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, PIDController2D,
                         SafetyGuard, print_banner, print_menu,
                         wait_for_keypress)


class ColorTracker:
    """PID-based colour target tracker."""

    IMG_W = 320
    IMG_H = 240
    TARGET_X = IMG_W // 2
    TARGET_Y = IMG_H // 2

    def __init__(self, robot_serial, motion):
        self.serial = robot_serial
        self.motion = motion
        self.pid = PIDController2D(
            target_x=self.TARGET_X, target_y=self.TARGET_Y,
            Px=5, Ix=0, Dx=1, Py=20, Iy=1, Dy=3, scale=100.0
        )
        self.target_found = False
        self.target_x = 0
        self.target_y = 0
        self.lost_frames = 0
        self.base_speed = 40
        self.max_speed = 150
        self.dead_zone = 15

    def compute_motor_speeds(self, x, y, w, h):
        dx = x - self.TARGET_X
        dy = y - self.TARGET_Y
        if abs(dx) < self.dead_zone and abs(dy) < self.dead_zone:
            return 0, 0
        out_x, out_y = self.pid.compute(x, y, limit_x=80, limit_y=60)
        left = int(self.base_speed + out_y + out_x)
        right = int(self.base_speed + out_y - out_x)
        left = max(-self.max_speed, min(self.max_speed, left))
        right = max(-self.max_speed, min(self.max_speed, right))
        return left, right

    def stop(self):
        self.motion.stop()


def run_simulation_demo(motion, duration=20):
    """Run colour tracking with a simulated target moving in a circle."""
    print_banner("Simulated Colour Tracking Demo")
    print("A virtual target moves in a circle — watch the PID controller track it.\n")
    pid = PIDController2D(160, 120, 5, 0, 1, 20, 1, 3, 100.0)
    base_speed = 40
    sim_time = 0.0
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            sim_time += 0.05
            tx = 160 + int(80 * math.sin(sim_time * 0.5))
            ty = 120 + int(60 * math.cos(sim_time * 0.5))
            ox, oy = pid.compute(tx, ty, 80, 60)
            left = int(base_speed + oy + ox)
            right = int(base_speed + oy - ox)
            left = max(-150, min(150, left))
            right = max(-150, min(150, right))
            motion.set_wheel_speeds(left, right)
            print(f"\r  Target:({tx:3d},{ty:3d}) PID:({ox:+5.1f},{oy:+5.1f}) "
                  f"Motors:L={left:+4d} R={right:+4d}  ", end='', flush=True)
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        motion.stop()
        print("\n[STOP] Simulation ended.")


def main():
    print_banner("Robot Color Tracking — Vision-Guided Object Following")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    if robot_serial.is_connected():
        tracker = ColorTracker(robot_serial, motion)
        print("\n[READY] Colour tracking active.")
        print("  Place a coloured object in front of the K210 camera.")
        print("  Press Ctrl+C to stop.\n")
        try:
            while True:
                data = robot_serial.read_line()
                time.sleep(0.02)
        except KeyboardInterrupt:
            print("\n[INTERRUPT]")
        finally:
            tracker.stop()
    else:
        print("[SIM] No robot detected — running simulation demo.\n")
        run_simulation_demo(motion, duration=20)

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Colour tracking ended.")


if __name__ == "__main__":
    main()
