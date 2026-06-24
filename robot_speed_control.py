# -*- coding: utf-8-*-# Encoding cookie added by Mu Editor
from microbit import display, Image, sleep
import tinybit

display.show(Image.HAPPY)

while True:
    tinybit.car_run(50, 50)
    sleep(100)
    tinybit.car_run(254, 254)
    sleep(100)
    tinybit.car_run(50, 50)
    sleep(100)
    tinybit.car_run(254, 254)
    sleep(100)
    tinybit.car_run(50, 50)
    sleep(100)
    tinybit.car_run(254, 254)
    sleep(100)


