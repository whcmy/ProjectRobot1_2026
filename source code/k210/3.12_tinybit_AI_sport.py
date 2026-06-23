import sensor, image, time, lcd, gc, cmath
from maix import KPU

from modules import ybserial
import time

kmdel = 1 #1:使用tinybit_AI_01.kmodel  2:tinybit_AI_02.kmodel

serial = ybserial()

lcd.init()                          # Init lcd display

# sensor.reset(dual_buff=True)      # improve fps
sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 1000)     # Wait for settings take effect.
clock = time.clock()                # Create a clock object to track the FPS.

print("ready load model")

sensor.set_auto_gain(True) #开启自动增益

kpu = KPU()

#训练的时候，标签的名称必须和label_num一致，标签的数量可少不可多
label_num = ["red","green","school","walk","one","right","two","freeSpeed","left","limitSpeed","horn"]#不能动此顺序

if kmdel ==1 :
    labels = ["one","two","freeSpeed","green","horn","limitSpeed","red","left","right"]
    anchor = (1.88, 1.61, 2.09, 2.03, 2.28, 2.25, 2.53, 2.53, 4.97, 5.25)
    kpu.load_kmodel('/sd/tinybit_AI_01.kmodel')

elif kmdel ==2 :
    labels = ["one","two","freeSpeed","green","horn","left","limitSpeed","red","right"]
    anchor = (1.78, 1.34, 2.03, 2.00, 2.19, 2.19, 2.41, 2.41, 2.69, 2.69)
    kpu.load_kmodel('/sd/tinybit_AI_02.kmodel')

kpu.init_yolo2(anchor, anchor_num=(int)(len(anchor)/2), img_w=320, img_h=240, net_w=320 , net_h=240 ,layer_w=10 ,layer_h=8, threshold=0.4, nms_value=0.3, classes=len(labels))

msg_ = ""

while(True):
    gc.collect() #清内存

    clock.tick()
    img = sensor.snapshot()

    kpu.run_with_output(img)
    dect = kpu.regionlayer_yolo2()

    fps = clock.fps()

    if len(dect) > 0:
        for l in dect :
            img.draw_rectangle(l[0],l[1],l[2],l[3],color=(0,255,0))
            info = "%s %.3f" % (labels[l[4]], l[5])
            img.draw_string(l[0],l[1],info,color=(255, 255, 0),scale=1.5)
            print(info)
            del info

            #idd = str(l[4]+1)
            msg_ = labels[l[4]]
            for i in range(len(label_num)):
                if msg_ == label_num[i]:
                    idd = str(i+1) #从1开始
                    print(idd)
                    break


    if len(dect) > 0:
       send_data ="$"+"09"+ idd+','+"#"
       time.sleep_ms(5)
       serial.send(send_data)
    else :
        serial.send("#")

    img.draw_string(0, 0, "%2.1ffps" %(fps),color=(0,60,255),scale=2.0)
    lcd.display(img)
