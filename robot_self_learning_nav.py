#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Self-Learning Navigation — Trainable Visual Classifier
==============================================================
Uses the K210's self-learning (few-shot learning) capability.
The robot can be trained to recognise custom objects/scenes
and navigate based on what it sees.

Workflow:
  1. INIT mode    — Prepare the system
  2. TRAIN mode   — Show examples of each class (3 classes)
  3. CLASSIFY mode — Robot navigates based on classification

Protocol (from K210):
  Receive: $10<class_id>,#  (1, 2, or 3)
  Send:    $20+Lxxx+Rxxx,#

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import os
import json
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class SelfLearningNavigator:
    """Navigates using the K210's self-learning classifier."""

    DEFAULT_MAPPINGS = {
        1: {"name": "Clear Path", "action": "forward", "speed": 80,
            "desc": "Path ahead is clear — go forward"},
        2: {"name": "Obstacle", "action": "avoid", "speed": 60,
            "desc": "Obstacle detected — turn away"},
        3: {"name": "Destination", "action": "stop", "speed": 0,
            "desc": "Destination reached — stop and celebrate"},
    }

    def __init__(self, motion):
        self.motion = motion
        self.mappings = dict(self.DEFAULT_MAPPINGS)
        self.current_class = None
        self.last_class = None
        self.class_count = {1: 0, 2: 0, 3: 0}
        self.default_speed = 80

    def set_mapping(self, class_id, name, action, speed=80, desc=""):
        if class_id not in (1, 2, 3):
            print(f"[ERROR] Class ID must be 1, 2, or 3")
            return
        self.mappings[class_id] = {"name": name, "action": action, "speed": speed, "desc": desc}
        print(f"[MAP] Class {class_id}: '{name}' -> {action}")

    def handle_classification(self, class_id):
        if class_id not in self.mappings:
            return
        mapping = self.mappings[class_id]
        action = mapping['action']
        speed = mapping['speed']
        self.current_class = class_id
        self.class_count[class_id] = self.class_count.get(class_id, 0) + 1
        if class_id != self.last_class:
            print(f"\n[LEARN] Class {class_id} ({mapping['name']}): {mapping['desc']} -> {action}")
            self.last_class = class_id
            self._execute_action(action, speed)

    def _execute_action(self, action, speed):
        if action == 'forward':
            self.motion.forward(speed)
        elif action == 'avoid':
            self.motion.turn_right(60)
            time.sleep(0.5)
            self.motion.forward(speed)
            time.sleep(1.5)
            self.motion.turn_left(60)
            time.sleep(0.5)
            self.motion.forward(speed)
        elif action == 'stop':
            self.motion.stop()
        elif action == 'turn_left':
            self.motion.turn_left(speed)
            time.sleep(0.5)
            self.motion.stop()
        elif action == 'turn_right':
            self.motion.turn_right(speed)
            time.sleep(0.5)
            self.motion.stop()
        elif action == 'backward':
            self.motion.backward(speed)
            time.sleep(1.0)
            self.motion.stop()
        elif action == 'dance':
            for _ in range(2):
                self.motion.turn_left(80)
                time.sleep(0.3)
                self.motion.turn_right(80)
                time.sleep(0.3)
            self.motion.stop()

    def show_mappings(self):
        print("\nSelf-Learning Class Mappings:")
        print(f"  {'ID':<4} {'Name':<15} {'Action':<12} {'Speed':<6} Description")
        print(f"  {'-'*55}")
        for cid in (1, 2, 3):
            m = self.mappings[cid]
            print(f"  {cid:<4} {m['name']:<15} {m['action']:<12} {m['speed']:<6} {m['desc']}")

    def show_stats(self):
        print("\nClassification Statistics:")
        for cid in (1, 2, 3):
            m = self.mappings[cid]
            count = self.class_count.get(cid, 0)
            bar = '#' * min(count, 40)
            print(f"  Class {cid} ({m['name']:<15s}): {count:3d} {bar}")

    def save_config(self, filepath="self_learn_config.json"):
        try:
            with open(filepath, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            print(f"[SAVE] Configuration saved to {filepath}")
        except IOError as e:
            print(f"[ERROR] {e}")

    def load_config(self, filepath="self_learn_config.json"):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    loaded = json.load(f)
                    self.mappings = {int(k): v for k, v in loaded.items()}
                print(f"[LOAD] Configuration loaded from {filepath}")
                self.show_mappings()
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"[ERROR] {e}")


def print_training_guide():
    print_banner("Self-Learning Training Guide")
    print("""
  The K210 self-learning system has 3 trainable classes.

  STEP 1 — INIT mode:
    Press the K210 BOOT button once to enter INIT mode.

  STEP 2 — TRAIN Class 1 (Clear Path):
    Press BOOT again -> "Train class 1"
    Show the camera a clear path -> press BOOT to capture.
    Capture 3-5 images. Auto-advances after 5 captures.

  STEP 3 — TRAIN Class 2 (Obstacle):
    Show obstacles -> capture 3-5 images.

  STEP 4 — TRAIN Class 3 (Destination):
    Show the destination marker -> capture 3-5 images.

  STEP 5 — CLASSIFY mode:
    The robot classifies what it sees and executes
    the mapped behaviour (forward / avoid / stop).

  TIP: Long-press BOOT to restart training at any time.
""")


def run_simulation_demo(motion):
    print_banner("Simulated Self-Learning Navigation Demo")
    navigator = SelfLearningNavigator(motion)
    navigator.show_mappings()
    sequence = [1, 1, 1, 2, 2, 1, 1, 2, 1, 3]
    print("\nSimulated classifications:")
    for cls in sequence:
        mapping = navigator.mappings[cls]
        print(f"  Class {cls} -> {mapping['name']}: {mapping['action']}")
        navigator.handle_classification(cls)
        time.sleep(1.5)
    motion.stop()
    navigator.show_stats()
    print("\n[DONE] Self-learning navigation demo complete.")


def main():
    print_banner("Robot Self-Learning Navigation — Trainable Classifier")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()
    navigator = SelfLearningNavigator(motion)

    menu_options = [
        ('1', 'Simulation demo'),
        ('2', 'Show training guide'),
        ('3', 'Show class mappings'),
        ('4', 'Configure class mapping'),
        ('5', 'Save / Load configuration'),
        ('6', 'Show statistics'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Self-Learning Navigation — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == '2':
            print_training_guide()
        elif choice == '3':
            navigator.show_mappings()
        elif choice == '4':
            try:
                cid = int(input("  Class ID (1/2/3): ").strip())
                name = input("  Name: ").strip()
                action = input("  Action (forward/avoid/stop/turn_left/turn_right/backward/dance): ").strip()
                spd = input("  Speed (0-150): ").strip()
                speed = int(spd) if spd else 80
                desc = input("  Description: ").strip()
                navigator.set_mapping(cid, name, action, speed, desc)
            except ValueError:
                print("Invalid input.")
        elif choice == '5':
            sub = input("  [s]ave or [l]oad config? ").strip().lower()
            if sub == 's':
                navigator.save_config()
            elif sub == 'l':
                navigator.load_config()
        elif choice == '6':
            navigator.show_stats()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Self-learning navigation ended.")


if __name__ == "__main__":
    main()
