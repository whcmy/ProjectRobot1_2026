import sensor, image, time, lcd

from modules import ybserial


min_speed = 15 #最小速度
ser = ybserial()

PIDx = (15, 0, 2)
PIDy = (20, 1, 3)
SCALE = 100.0


class PID(object):
    def __init__(self, target, P, I, D):

        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.setPoint = target
        self.err = 0
        self.err_next = 0
        self.err_last = 0
        self.last_result = 0


    def __del__(self):
        print("DEL PID")

    # 重新设置目标值
    def reset_target(self, target):
        self.setPoint = target


    # 增量式PID计算方式
    def incremental(self, current_value,xory, limit=0):
        if  xory == "x":
            self.err = current_value - self.setPoint
        elif xory == "y":
            self.err =  self.setPoint - current_value
        result = self.last_result + self.Kp * (self.err - self.err_next) + self.Ki * self.err + self.Kd * (self.err - 2 * self.err_next + self.err_last)
        self.err_last = self.err_next
        self.err_next = self.err
        if limit > 0:
            if result > limit:
                result = limit
            if result < -limit:
                result = -limit
        self.last_result = result
        return result


def deal_data_speed(revaule_x,revaule_y):

    speed_L = revaule_y + 0 + revaule_x
    speed_R = revaule_y - 0 - revaule_x

    speed_L = int(speed_L)
    speed_R = int(speed_R)
    print(speed_L)

    #控制最小速度（左电机）
    if((speed_L > -min_speed) and (speed_L<0)):
        speed_L = speed_L-min_speed
    elif((speed_L < min_speed) and (speed_L>0)):
        speed_L  = speed_L+min_speed

    #控制最小速度（右电机）
    if((speed_R > -min_speed) and (speed_R<0)):
        speed_R = speed_R-min_speed
    elif((speed_R < min_speed) and (speed_R>0)):
        speed_R  = speed_R+min_speed



    #数据处理（左电机）
    if(speed_L<0):
        speedstr_l = str(-speed_L)
        if len(speedstr_l)<3 :
            i_flag = 3-len(speedstr_l)
            speedstr_l = "-"+"0"*i_flag + speedstr_l
        else :
            speedstr_l = "-"+speedstr_l
    else:
        speedstr_l = str(speed_L)
        if len(speedstr_l)<3 :
            i_flag = 3-len(speedstr_l)
            speedstr_l = "+"+"0"*i_flag + speedstr_l
        else :
            speedstr_l = "+"+speedstr_l

    #数据处理（右电机）
    if(speed_R<0):
        speedstr_r = str(-speed_R)
        if len(speedstr_r)<3 :
            i_flag = 3-len(speedstr_r)
            speedstr_r = "-"+"0"*i_flag + speedstr_r
        else :
            speedstr_r = "-"+speedstr_r
    else:
        speedstr_r = str(speed_R)
        if len(speedstr_r)<3 :
            i_flag = 3-len(speedstr_r)
            speedstr_r = "+"+"0"*i_flag + speedstr_r
        else :
            speedstr_r = "+"+speedstr_r

    send_buf = "$20"+speedstr_l+speedstr_r+",#"
    ser.send(send_buf)
    print(send_buf)


PID_x = PID(
    160,
    PIDx[0] / 1.0 / (SCALE),
    PIDx[1] / 1.0 / (SCALE),
    PIDx[2] / 1.0 / (SCALE))

PID_y = PID(
    120,
    PIDy[0] / 1.0 / (SCALE),
    PIDy[1] / 1.0 / (SCALE),
    PIDy[2] / 1.0 / (SCALE))








lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 100)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()

print("Hold the object you want to track in front of the camera in the box.")
print("MAKE SURE THE COLOR OF THE OBJECT YOU WANT TO TRACK IS FULLY ENCLOSED BY THE BOX!")

# Capture the color thresholds for whatever was in the center of the image.
# 50x50 center of QVGA.
BOX = 30
r = [(320//2)-(BOX//2), (240//2)-(BOX//2), BOX, BOX]
for i in range(50):
    img = sensor.snapshot()
    img.draw_rectangle(r)
    lcd.display(img)

print("Learning thresholds...")
threshold = [50, 50, 0, 0, 0, 0] # Middle L, A, B values.

for i in range(50):
    img = sensor.snapshot()
    hist = img.get_histogram(roi=r)
    lo = hist.get_percentile(0.01) # Get the CDF of the histogram at the 1% range (ADJUST AS NECESSARY)!
    hi = hist.get_percentile(0.99) # Get the CDF of the histogram at the 99% range (ADJUST AS NECESSARY)!
    # Average in percentile values.
    threshold[0] = (threshold[0] + lo.l_value()) // 2
    threshold[1] = (threshold[1] + hi.l_value()) // 2
    threshold[2] = (threshold[2] + lo.a_value()) // 2
    threshold[3] = (threshold[3] + hi.a_value()) // 2
    threshold[4] = (threshold[4] + lo.b_value()) // 2
    threshold[5] = (threshold[5] + hi.b_value()) // 2
    for blob in img.find_blobs([threshold], pixels_threshold=100, area_threshold=100, merge=True, margin=10):
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        img.draw_rectangle(r, color=(0,255,0))
    lcd.display(img)

#threshold = [10, 44, -22, 15, 13, 41]
print("threshold:", threshold)
print("Thresholds learned...")
print("Start Color Recognition...")
state = 0
limit_a = 80

while(True):
    clock.tick()
    img = sensor.snapshot()
    fps = clock.fps()
    data_in = 0
    index = 0
    for blob in img.find_blobs([threshold], pixels_threshold=100, area_threshold=150, merge=True, margin=10):
        #img.draw_rectangle(blob.rect())
        #img.draw_cross(blob.cx(), blob.cy())
        index = index + 1
        #print("blob:", index, blob.w(), blob.h())
        if index == 1:
            area_max = blob.w()*blob.h()
            area = blob
        else:
            temp_area = blob.w()*blob.h()
            if temp_area > area_max:
                area_max = temp_area
                area = blob
        state = 1

    if state == 1:
        #print("area:", index, area.w(), area.h())
        img.draw_rectangle(area.rect())
        img.draw_cross(area.cx(), area.cy())
        value_x = PID_x.incremental(blob.cx(),"x")
        value_y = PID_y.incremental(blob.cy(),"y")
        deal_data_speed(value_x,value_y)
        print("value:", value_x, value_y)
        state = 2
    elif state == 2:
        ser.send("#")#发停止信号
        state = 0
    img.draw_string(0, 0, "%2.1ffps" %(fps), color=(0, 60, 128), scale=2.0)
    lcd.display(img)
    #print("FPS:s", fps)
    #bot.set_car_motion(0, 0, value)
