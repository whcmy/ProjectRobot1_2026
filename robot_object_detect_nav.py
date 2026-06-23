#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Object Detection Navigation — Vision-Based Scene Understanding
======================================================================
Uses the K210's YOLO object detection to recognise objects
in the environment and navigate accordingly.

Detected Object Behaviours:
  - Person          -> Stop and wait
  - Car / Bus       -> Avoid (turn away)
  - Bicycle / Bike  -> Follow
  - Cat / Dog       -> Approach slowly
  - Traffic signs   -> Obey (stop, turn, speed change)

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class ObjectDetectionNavigator:
    """Navigates based on detected objects in the camera frame."""

    VOC_LABELS = [
        "aeroplane", "bicycle", "bird", "boat", "bottle",
        "bus", "car", "cat", "chair", "cow",
        "diningtable", "dog", "horse", "motorbike", "person",
        "pottedplant", "sheep", "sofa", "train", "tvmonitor"
    ]

    VOC_BEHAVIOURS = {
        "person": "stop_wait", "bicycle": "follow", "car": "avoid_right",
        "motorbike": "follow", "bus": "avoid_left", "train": "stop_wait",
        "cat": "approach_slow", "dog": "approach_slow",
        "chair": "avoid_right", "sofa": "avoid_left",
        "bottle": "push", "cow": "stop_wait", "horse": "stop_wait",
        "sheep": "stop_wait", "diningtable": "avoid_right",
        "pottedplant": "avoid_right",
    }

    def __init__(self, motion):
        self.motion = motion
        self.current_object = None
        self.detection_count = {}
        self.default_speed = 80

    def handle_detection(self, object_label):
        self.detection_count[object_label] = self.detection_count.get(object_label, 0) + 1
        self.current_object = object_label
        behaviour = self.VOC_BEHAVIOURS.get(object_label, "ignore")
        print(f"[DETECT] {object_label:>15s} -> {behaviour}")
        self._execute_behaviour(behaviour)

    def _execute_behaviour(self, behaviour):
        if behaviour == "stop_wait":
            self.motion.stop()
            time.sleep(1.5)
        elif behaviour == "forward":
            self.motion.forward(self.default_speed)
        elif behaviour == "avoid_right":
            self.motion.turn_right(60)
            time.sleep(0.5)
            self.motion.forward(self.default_speed)
            time.sleep(1.0)
            self.motion.turn_left(60)
            time.sleep(0.5)
        elif behaviour == "avoid_left":
            self.motion.turn_left(60)
            time.sleep(0.5)
            self.motion.forward(self.default_speed)
            time.sleep(1.0)
            self.motion.turn_right(60)
            time.sleep(0.5)
        elif behaviour == "follow":
            self.motion.forward(int(self.default_speed * 0.7))
        elif behaviour == "approach_slow":
            self.motion.forward(40)
        elif behaviour == "push":
            self.motion.forward(50)
            time.sleep(1.0)
            self.motion.stop()

    def show_stats(self):
        if not self.detection_count:
            print("No objects detected yet.")
            return
        print("\nDetection Statistics:")
        for obj, count in sorted(self.detection_count.items(), key=lambda x: x[1], reverse=True):
            bar = '#' * min(count, 30)
            print(f"  {obj:>15s}: {count:3d} {bar}")


def run_simulation_demo(motion):
    print_banner("Simulated Object Detection Navigation Demo")
    navigator = ObjectDetectionNavigator(motion)
    detections = ["person", "bicycle", "car", "chair", "dog", "bottle", "bus", "cat"]
    for obj in detections:
        print(f"\n--- Camera sees: {obj} ---")
        navigator.handle_detection(obj)
        time.sleep(2.0)
    motion.stop()
    navigator.show_stats()
    print("\n[DONE] Object detection demo complete.")


def main():
    print_banner("Robot Object Detection Navigation — Scene Understanding")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()
    navigator = ObjectDetectionNavigator(motion)

    menu_options = [
        ('1', 'VOC object detection simulation demo'),
        ('2', 'Detection statistics'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Object Detection Nav — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == '2':
            navigator.show_stats()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Object detection navigation ended.")


if __name__ == "__main__":
    main()
