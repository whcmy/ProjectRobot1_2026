# -*- coding: utf-8 -*-
"""
Robot Basic Move — micro:bit Button-Controlled Movement
========================================================
Uses micro:bit buttons to control the Tinybit car.
Press A+B together to stop.

Controls:
  Button A      — Turn left (spin left wheel backward)
  Button B      — Turn right (spin right wheel backward)
  Button A+B    — Forward
  Button A(long)— Backward
  Shake gesture — Stop

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, button_a, button_b, accelerometer, sleep
import tinybit

# --- Configuration ---
SPEED_SLOW = 40
SPEED_MED = 80
SPEED_FAST = 120

# --- Main loop ---
display.show(Image.ARROW_N)

while True:
    a_pressed = button_a.is_pressed()
    b_pressed = button_b.is_pressed()

    if accelerometer.was_gesture("shake"):
        tinybit.car_run(0, 0)
        display.show(Image.NO)

    elif a_pressed and b_pressed:
        tinybit.car_run(SPEED_MED, SPEED_MED)
        display.show(Image.ARROW_N)

    elif a_pressed:
        tinybit.car_run(-SPEED_SLOW, SPEED_SLOW)
        display.show(Image.ARROW_W)

    elif b_pressed:
        tinybit.car_run(SPEED_SLOW, -SPEED_SLOW)
        display.show(Image.ARROW_E)

    else:
        tinybit.car_run(0, 0)
        display.show(Image.HAPPY)

    sleep(50)
