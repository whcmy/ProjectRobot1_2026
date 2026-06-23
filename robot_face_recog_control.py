#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Face Recognition Control — Identity-Based Access
========================================================
Uses the K210's face recognition capability to:
  - Register authorised users' faces
  - Recognise registered users and grant access
  - Execute identity-specific behaviours (greet, follow, dance, stop)

Protocol (from K210):
  Receive: $08<result>,<id>,#
  Send:    $20+Lxxx+Rxxx,#

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import json
import os
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class FaceRecognitionController:
    """Controls the robot based on face recognition results."""

    def __init__(self, motion, robot_serial):
        self.motion = motion
        self.serial = robot_serial
        self.users = {}
        self.last_recognition_time = 0
        self.recognition_cooldown = 1.0
        self.access_control_enabled = False
        self._load_users()

    def _load_users(self, filepath="face_users.json"):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    self.users = json.load(f)
                print(f"[LOAD] {len(self.users)} users loaded.")
            except (json.JSONDecodeError, IOError):
                self.users = {}
        else:
            self.users = {
                "00": {"name": "Alice", "permissions": "full", "behaviour": "follow"},
                "01": {"name": "Bob", "permissions": "limited", "behaviour": "greet"},
                "02": {"name": "Charlie", "permissions": "full", "behaviour": "dance"},
            }

    def _save_users(self, filepath="face_users.json"):
        try:
            with open(filepath, 'w') as f:
                json.dump(self.users, f, indent=2)
            print(f"[SAVE] Users saved.")
        except IOError as e:
            print(f"[ERROR] {e}")

    def register_user(self, user_id, name, permissions="full", behaviour="greet"):
        self.users[user_id] = {"name": name, "permissions": permissions, "behaviour": behaviour}
        self._save_users()
        print(f"[REGISTER] User {user_id} ({name}) added.")

    def remove_user(self, user_id):
        if user_id in self.users:
            name = self.users[user_id]['name']
            del self.users[user_id]
            self._save_users()
            print(f"[REMOVE] User {user_id} ({name}) removed.")

    def handle_recognition(self, recognised, user_id):
        now = time.time()
        if now - self.last_recognition_time < self.recognition_cooldown:
            return
        self.last_recognition_time = now
        if recognised and user_id in self.users:
            user = self.users[user_id]
            print(f"\n[FACE] Recognised: {user['name']} (ID={user_id})")
            self._execute_behaviour(user)
        elif recognised:
            print(f"\n[FACE] Recognised ID={user_id} (not in database)")
        else:
            print(f"\n[FACE] Unknown face detected")
            if self.access_control_enabled:
                print("  Access denied — backing away")
                self.motion.backward(60)
                time.sleep(0.5)
                self.motion.stop()

    def _execute_behaviour(self, user):
        behaviour = user.get('behaviour', 'greet')
        name = user.get('name', 'User')
        if behaviour == 'greet':
            print(f"  Greeting {name}")
            self.motion.forward(60)
            time.sleep(0.3)
            self.motion.backward(60)
            time.sleep(0.3)
            self.motion.stop()
        elif behaviour == 'follow':
            print(f"  Following {name}")
            self.motion.forward(50)
            time.sleep(0.5)
            self.motion.stop()
        elif behaviour == 'dance':
            print(f"  Dancing for {name}!")
            for _ in range(2):
                self.motion.turn_left(80)
                time.sleep(0.3)
                self.motion.turn_right(80)
                time.sleep(0.3)
            self.motion.stop()
        elif behaviour == 'stop':
            self.motion.stop()

    def list_users(self):
        if not self.users:
            print("No registered users.")
            return
        print("\nRegistered Users:")
        for uid, data in self.users.items():
            print(f"  ID={uid}: {data['name']} ({data['behaviour']})")


def run_simulation_demo(motion, controller):
    print_banner("Simulated Face Recognition Demo")
    scenarios = [
        (True, "00", "Alice approaches"),
        (True, "01", "Bob approaches"),
        (False, None, "Unknown person approaches"),
        (True, "02", "Charlie approaches"),
    ]
    for recognised, user_id, description in scenarios:
        print(f"\n--- {description} ---")
        controller.handle_recognition(recognised, user_id)
        time.sleep(2.0)
    motion.stop()
    print("\n[DONE] Face recognition demo complete.")


def main():
    print_banner("Robot Face Recognition Control — Identity-Based Access")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()
    controller = FaceRecognitionController(motion, robot_serial)

    menu_options = [
        ('1', 'Run simulation demo'),
        ('2', 'List registered users'),
        ('3', 'Register a new user'),
        ('4', 'Toggle access control mode'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Face Recognition — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion, controller)
        elif choice == '2':
            controller.list_users()
        elif choice == '3':
            uid = input("  User ID (2-digit): ").strip()
            name = input("  Name: ").strip()
            bh = input("  Behaviour (greet/follow/dance/stop): ").strip()
            controller.register_user(uid, name, behaviour=bh)
        elif choice == '4':
            controller.access_control_enabled = not controller.access_control_enabled
            state = "ON" if controller.access_control_enabled else "OFF"
            print(f"  Access control: {state}")
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Face recognition control ended.")


if __name__ == "__main__":
    main()
