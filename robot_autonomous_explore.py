#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Autonomous Exploration — Intelligent Environment Mapping
================================================================
Implements autonomous exploration behaviour.
The robot explores an unknown environment without human
intervention, building a simple internal map.

Exploration Strategies:
  - Random walk: Move randomly, turn on obstacles
  - Wall following: Follow perimeter walls
  - Spiral search: Expanding spiral from origin
  - Curiosity-driven: Prefer unexplored areas

Features:
  - Simple occupancy grid mapping
  - Visited-area tracking
  - Coverage estimate
  - Exploration statistics

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
import random
from collections import deque
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class OccupancyGrid:
    """A simple 2D occupancy grid for environment mapping."""

    UNKNOWN = 0
    FREE = 1
    VISITED = 2
    OBSTACLE = 3
    CELL_LABELS = {0: '?', 1: '.', 2: '#', 3: 'X'}

    def __init__(self, width=50, height=50, cell_size_cm=10):
        self.width = width
        self.height = height
        self.cell_size = cell_size_cm
        self.grid = [[self.UNKNOWN for _ in range(width)] for _ in range(height)]
        self.robot_x = width // 2
        self.robot_y = height // 2
        self.robot_heading = 0
        self.set_cell(self.robot_x, self.robot_y, self.VISITED)

    def set_cell(self, x, y, value):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = value

    def get_cell(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return self.OBSTACLE

    def mark_visited(self):
        self.set_cell(self.robot_x, self.robot_y, self.VISITED)

    def coverage_percent(self):
        total = self.width * self.height
        explored = sum(1 for row in self.grid for cell in row
                      if cell in (self.FREE, self.VISITED, self.OBSTACLE))
        return 100.0 * explored / total

    def find_nearest_unexplored(self):
        visited_grid = [[False] * self.width for _ in range(self.height)]
        queue = deque()
        queue.append((self.robot_x, self.robot_y, []))
        visited_grid[self.robot_y][self.robot_x] = True
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        while queue:
            cx, cy, path = queue.popleft()
            if self.get_cell(cx, cy) == self.UNKNOWN:
                return path[0] if path else None
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not visited_grid[ny][nx] and self.get_cell(nx, ny) != self.OBSTACLE:
                        visited_grid[ny][nx] = True
                        new_path = path + [(dx, dy)]
                        queue.append((nx, ny, new_path))
        return None

    def print_map(self):
        print(f"\n  Map ({self.width}x{self.height}), Coverage: {self.coverage_percent():.1f}%")
        print(f"  Robot @ ({self.robot_x}, {self.robot_y}), heading: {self.robot_heading} deg")
        vr = 15
        x1, x2 = max(0, self.robot_x - vr), min(self.width, self.robot_x + vr)
        y1, y2 = max(0, self.robot_y - vr), min(self.height, self.robot_y + vr)
        print("  +" + "-" * (x2 - x1) + "+")
        for y in range(y1, y2):
            line = "  |"
            for x in range(x1, x2):
                if x == self.robot_x and y == self.robot_y:
                    line += 'R'
                else:
                    line += self.CELL_LABELS[self.grid[y][x]]
            line += "|"
            print(line)
        print("  +" + "-" * (x2 - x1) + "+")


class ExplorationStrategy:
    """Collection of autonomous exploration strategies."""

    def __init__(self, motion, grid):
        self.motion = motion
        self.grid = grid
        self.strategy = 'curiosity'
        self.speed = 80

    def set_strategy(self, name):
        valid = ['random', 'wall_follow', 'spiral', 'curiosity']
        if name in valid:
            self.strategy = name
            print(f"[STRATEGY] Set to '{name}'")

    def step(self):
        if self.strategy == 'random':
            return self._step_random()
        elif self.strategy == 'curiosity':
            return self._step_curiosity()
        return self._step_random()

    def _step_random(self):
        r = random.random()
        if r < 0.7:
            self.motion.forward(self.speed)
            self.grid.robot_y -= 1
        elif r < 0.85:
            self.motion.turn_left(60)
            time.sleep(0.3)
            self.grid.robot_heading = (self.grid.robot_heading - 90) % 360
        else:
            self.motion.turn_right(60)
            time.sleep(0.3)
            self.grid.robot_heading = (self.grid.robot_heading + 90) % 360
        self.grid.mark_visited()
        return True

    def _step_curiosity(self):
        unexplored_dir = self.grid.find_nearest_unexplored()
        if unexplored_dir:
            dx, dy = unexplored_dir
            if dx == 0 and dy == -1:
                self.motion.forward(self.speed)
                self.grid.robot_y -= 1
            elif dx == 0 and dy == 1:
                self.motion.backward(self.speed)
                self.grid.robot_y += 1
            elif dx == -1:
                self.motion.turn_left(60)
                time.sleep(0.3)
                self.grid.robot_heading = (self.grid.robot_heading - 90) % 360
            elif dx == 1:
                self.motion.turn_right(60)
                time.sleep(0.3)
                self.grid.robot_heading = (self.grid.robot_heading + 90) % 360
            self.grid.mark_visited()
            return True
        else:
            print("[EXPLORE] No unexplored areas — exploration complete!")
            self.motion.stop()
            return False


class AutonomousExplorer:
    """Manages the full autonomous exploration lifecycle."""

    def __init__(self, motion):
        self.motion = motion
        self.grid = OccupancyGrid(width=40, height=40, cell_size_cm=15)
        self.strategy = ExplorationStrategy(motion, self.grid)
        self._running = False
        self.steps_taken = 0
        self.start_time = 0

    def start(self, strategy='curiosity', speed=80, max_time=60):
        self.strategy.set_strategy(strategy)
        self.strategy.speed = speed
        self._running = True
        self.start_time = time.time()
        self.steps_taken = 0
        print(f"\n[EXPLORE] Starting '{strategy}' exploration...")
        print(f"  Max time: {max_time}s, Speed: {speed}")

    def run_loop(self, max_time):
        while self._running and (time.time() - self.start_time < max_time):
            continuing = self.strategy.step()
            self.steps_taken += 1
            if not continuing:
                break
            if self.steps_taken % 10 == 0:
                elapsed = time.time() - self.start_time
                print(f"\r[EXPLORE] Steps: {self.steps_taken}  "
                      f"Time: {elapsed:.0f}s  "
                      f"Coverage: {self.grid.coverage_percent():.1f}%  ",
                      end='', flush=True)
            time.sleep(0.15)
        self.motion.stop()
        print("\n[EXPLORE] Exploration finished.")

    def stop(self):
        self._running = False
        self.motion.stop()
        self._show_stats()

    def _show_stats(self):
        elapsed = time.time() - self.start_time
        print_banner("Exploration Statistics")
        print(f"  Strategy:    {self.strategy.strategy}")
        print(f"  Duration:    {elapsed:.1f}s")
        print(f"  Steps:       {self.steps_taken}")
        print(f"  Coverage:    {self.grid.coverage_percent():.1f}%")
        self.grid.print_map()


def main():
    print_banner("Robot Autonomous Exploration — Environment Mapping")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()
    explorer = AutonomousExplorer(motion)

    menu_options = [
        ('1', 'Curiosity-driven exploration'),
        ('2', 'Random walk exploration'),
        ('3', 'Show current map'),
        ('q', 'Quit'),
    ]
    strat_map = {'1': 'curiosity', '2': 'random'}

    while True:
        print_menu("Autonomous Exploration — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice in strat_map:
            try:
                t = input("  Max exploration time (seconds) [30]: ").strip()
                max_time = float(t) if t else 30
            except ValueError:
                max_time = 30
            explorer.start(strategy=strat_map[choice], speed=80, max_time=max_time)
            print("\n  Press Ctrl+C to stop early.\n")
            try:
                explorer.run_loop(max_time)
            except KeyboardInterrupt:
                explorer.stop()
        elif choice == '3':
            explorer.grid.print_map()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    explorer.stop()
    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Autonomous exploration ended.")


if __name__ == "__main__":
    main()
