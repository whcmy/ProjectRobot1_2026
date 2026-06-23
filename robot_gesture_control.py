#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Gesture Control — Hand Signal Command Interface
=======================================================
Implements gesture-based robot control using face position
as a proxy for hand gestures.

Gesture Command Mapping:
  - Face detected (centre)    -> Stop
  - Face detected (left)      -> Turn left
  - Face detected (right)     -> Turn right
  - Face detected (top)       -> Forward
  - Face detected (bottom)    -> Backward
  - Mask ON                   -> Slow speed
  - Mask OFF                  -> Normal speed

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class GestureController:
    """Maps visual signals to robot movement commands."""

    CMD_STOP = "stop"
    CMD_FORWARD = "forward"
    CMD_BACKWARD = "backward"
    CMD_LEFT = "left"
    CMD_RIGHT = "right"
    CMD_DANCE = "dance"

    def __init__(self, motion):
        self.motion = motion
        self.default_speed = 80
        self.slow_speed = 40
        self.current_gesture = None
        self.last_command_time = 0
        self.command_cooldown = 0.3

    def interpret_face_position(self, x, y, w, h, img_w=320, img_h=240):
        cx = x + w // 2
        cy = y + h // 2
        left_thresh = img_w // 3
        right_thresh = 2 * img_w // 3
        top_thresh = img_h // 3
        bottom_thresh = 2 * img_h // 3

        if cx < left_thresh:
            h_zone = 'left'
        elif cx > right_thresh:
            h_zone = 'right'
        else:
            h_zone = 'centre'
        if cy < top_thresh:
            v_zone = 'top'
        elif cy > bottom_thresh:
            v_zone = 'bottom'
        else:
            v_zone = 'mid'

        zone_commands = {
            ('left', 'mid'): self.CMD_LEFT, ('right', 'mid'): self.CMD_RIGHT,
            ('centre', 'top'): self.CMD_FORWARD, ('centre', 'mid'): self.CMD_STOP,
            ('centre', 'bottom'): self.CMD_BACKWARD,
            ('left', 'top'): self.CMD_LEFT, ('right', 'top'): self.CMD_RIGHT,
            ('left', 'bottom'): self.CMD_BACKWARD, ('right', 'bottom'): self.CMD_BACKWARD,
        }
        return zone_commands.get((h_zone, v_zone), self.CMD_STOP)

    def execute_gesture(self, command, speed=None):
        now = time.time()
        if now - self.last_command_time < self.command_cooldown:
            return
        self.last_command_time = now
        s = speed if speed is not None else self.default_speed
        self.current_gesture = command

        if command == self.CMD_STOP:
            self.motion.stop()
        elif command == self.CMD_FORWARD:
            self.motion.forward(s)
        elif command == self.CMD_BACKWARD:
            self.motion.backward(s)
        elif command == self.CMD_LEFT:
            self.motion.turn_left(s)
        elif command == self.CMD_RIGHT:
            self.motion.turn_right(s)
        elif command == self.CMD_DANCE:
            for _ in range(2):
                self.motion.turn_left(80)
                time.sleep(0.3)
                self.motion.turn_right(80)
                time.sleep(0.3)
            self.motion.stop()
        print(f"\r[GESTURE] {command:12s} speed={s:3d}  ", end='', flush=True)


def run_simulation_demo(motion):
    print_banner("Simulated Gesture Control Demo")
    controller = GestureController(motion)
    # Simulated face positions: (x, y, w, h)
    gestures = [
        (160, 120, 50, 50),   # Centre -> Stop
        (160, 60, 50, 50),    # Top -> Forward
        (60, 120, 50, 50),    # Left -> Left
        (260, 120, 50, 50),   # Right -> Right
        (160, 180, 50, 50),   # Bottom -> Backward
    ]
    print("Cycling through gesture positions:\n")
    for _ in range(3):
        for x, y, w, h in gestures:
            cmd = controller.interpret_face_position(x, y, w, h)
            controller.execute_gesture(cmd)
            zone = "CENTRE"
            if x < 107:
                zone = "LEFT"
            elif x > 213:
                zone = "RIGHT"
            if y < 80:
                zone += "-TOP"
            elif y > 160:
                zone += "-BOTTOM"
            print(f"\r  Face @ ({x:3d},{y:3d}) -> Zone: {zone:12s} | CMD: {cmd:10s}", end='')
            time.sleep(1.5)
    motion.stop()
    print("\n\n[DONE] Gesture control demo complete.")


def main():
    print_banner("Robot Gesture Control — Hand Signal Command Interface")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    menu_options = [
        ('1', 'Simulation demo (auto-cycling gestures)'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Gesture Control — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Gesture control ended.")


if __name__ == "__main__":
    main()
