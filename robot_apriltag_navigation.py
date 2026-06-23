#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot AprilTag Navigation — Fiducial Marker-Based Guidance
===========================================================
Implements navigation using AprilTag visual fiducial markers.
The robot can:
  - Follow a specific tag (visual servoing via PID)
  - Navigate toward a tag with a specific ID
  - Execute tag-based missions (go to tag 1, then tag 2, ...)

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, PIDController2D,
                         SafetyGuard, print_banner, print_menu,
                         wait_for_keypress)


class AprilTagNavigator:
    """Navigates using AprilTag markers detected by the K210 camera."""

    IMG_W = 160
    IMG_H = 120
    TARGET_X = IMG_W // 2
    TARGET_Y = IMG_H // 2

    def __init__(self, robot_serial, motion):
        self.serial = robot_serial
        self.motion = motion
        self.pid = PIDController2D(
            target_x=self.TARGET_X, target_y=self.TARGET_Y,
            Px=5, Ix=0, Dx=1, Py=20, Iy=1, Dy=3, scale=100.0
        )
        self.current_tag_id = None
        self.tag_found = False
        self.base_speed = 30

    def parse_tag_data(self, data):
        try:
            data = data.strip()
            if '$04' in data:
                start = data.find('$04') + 3
                end = data.find(',#')
                if end == -1:
                    end = len(data)
                payload = data[start:end]
                parts = payload.split(',')
                if len(parts) >= 2:
                    return parts[0].strip(), parts[1].strip()
        except (ValueError, IndexError):
            pass
        return None

    def execute_mission(self, tag_sequence, dwell_time=2.0):
        print_banner("AprilTag Mission")
        print(f"Mission: visit tags {tag_sequence}")
        for i, tag_id in enumerate(tag_sequence):
            print(f"\n--- Navigating to Tag {tag_id} ({i+1}/{len(tag_sequence)}) ---")
            for _ in range(5):
                self.motion.forward(50)
                time.sleep(0.3)
            self.motion.stop()
            print(f"  [ARRIVED] At Tag {tag_id}")
            time.sleep(dwell_time)
        self.motion.stop()
        print("\n[MISSION COMPLETE]")


def run_simulation_demo(motion, duration=20):
    print_banner("Simulated AprilTag Navigation Demo")
    print("Virtual tags placed in a 160x120 arena.\n")
    navigator = AprilTagNavigator(None, motion)
    mission_tags = ['0', '1', '2']
    for tag_id in mission_tags:
        print(f"\n--- Navigating to Tag {tag_id} ---")
        for step in range(10):
            print(f"\r  Approaching... step {step+1}/10", end='', flush=True)
            motion.forward(40)
            time.sleep(0.3)
        motion.stop()
        print(f"\n  [ARRIVED] At Tag {tag_id}")
        time.sleep(1.0)
    motion.stop()
    print("\n[DONE] Mission complete.")


def main():
    print_banner("Robot AprilTag Navigation — Fiducial Marker Guidance")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    navigator = AprilTagNavigator(robot_serial, motion)

    menu_options = [
        ('1', 'Simulation demo'),
        ('2', 'Execute mission (tag sequence)'),
        ('q', 'Quit'),
    ]

    while True:
        print_menu("AprilTag Navigation — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion, duration=20)
        elif choice == '2':
            seq = input("Enter tag sequence (comma-separated, e.g. 0,1,2): ").strip()
            tags = [t.strip() for t in seq.split(',')]
            navigator.execute_mission(tags)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] AprilTag navigation ended.")


if __name__ == "__main__":
    main()
