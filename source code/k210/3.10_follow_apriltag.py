import sensor, image, time, math, lcd
from modules import ybserial


ser = ybserial()
min_speed = 20 #最小速度  46

PIDx = (5, 0, 1)
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



    #数据处理（左电机） 新电机方向是反的所以+就是-
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

    #数据处理（右电机）新电机方向是反的所以+就是-
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
    80,
    PIDx[0] / 1.0 / (SCALE),
    PIDx[1] / 1.0 / (SCALE),
    PIDx[2] / 1.0 / (SCALE))

PID_y = PID(
    60,
    PIDy[0] / 1.0 / (SCALE),
    PIDy[1] / 1.0 / (SCALE),
    PIDy[2] / 1.0 / (SCALE))


lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
#sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 100)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()


tag_families = 0
tag_families |= image.TAG16H5   # comment out to disable this family
tag_families |= image.TAG25H7   # comment out to disable this family
tag_families |= image.TAG25H9   # comment out to disable this family
tag_families |= image.TAG36H10  # comment out to disable this family
tag_families |= image.TAG36H11  # comment out to disable this family (default family)
tag_families |= image.ARTOOLKIT # comment out to disable this family


def family_name(tag):
    if(tag.family() == image.TAG16H5):
        return "TAG16H5"
    if(tag.family() == image.TAG25H7):
        return "TAG25H7"
    if(tag.family() == image.TAG25H9):
        return "TAG25H9"
    if(tag.family() == image.TAG36H10):
        return "TAG36H10"
    if(tag.family() == image.TAG36H11):
        return "TAG36H11"
    if(tag.family() == image.ARTOOLKIT):
        return "ARTOOLKIT"

state = 0

while(True):
    clock.tick()
    img = sensor.snapshot()
    fps = clock.fps()
    #img = img.resize(292, 210)
    index = 0
    for tag in img.find_apriltags(families=tag_families):
        index = index + 1
        #img.draw_rectangle(tag.rect(), color = (255, 0, 0))
        #img.draw_cross(tag.cx(), tag.cy(), color = (0, 255, 0))
        #print_args = (family_name(tag), tag.id(), (180 * tag.rotation()) / math.pi)
        #print("Tag Family %s, Tag ID %d, rotation %f (degrees)" % print_args)
        if index == 1:
            tag_max = tag.w()*tag.h()
            tag1 = tag
        else:
            temp = tag.w()*tag.h()
            if temp > tag_max:
                tag_max = temp
                tag1 = tag
        state = 1

    if state == 1:
        #print("area:", index, area.w(), area.h())
        img.draw_rectangle(tag1.rect(), color = (255, 0, 0))
        img.draw_cross(tag1.cx(), tag1.cy(), color = (0, 255, 0))
        value_x = PID_x.incremental(tag1.cx(),"x")
        value_y = PID_y.incremental(tag1.cy(),"y")
        deal_data_speed(value_x,value_y)
        print("value:", value_x, value_y)
        state = 2
    elif state == 2:
        ser.send("#")#发停止信号
        state = 0
    img.draw_string(0, 0, "%2.1ffps" %(fps), color=(0, 60, 128), scale=1.0)
    lcd.display(img)
    #print(fps)
