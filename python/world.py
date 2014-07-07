from PIL import Image, ImageTk
import math
# import Image
import Tkinter
# import turtle
from turtle import RawTurtle, TurtleScreen
import random
import json
import os
# import time
import numpy as np

root = Tkinter.Tk()
canvas = Tkinter.Canvas(root, width=1200, height=264, state=Tkinter.DISABLED)
canvas.pack()
screen = TurtleScreen(canvas)
turtle = RawTurtle(screen)
# screen.setworldcoordinates(0, 399, 999, 0)
turtle.hideturtle()
turtle.up()
turtle.tracer(50000, delay=0)
# turtle.register_shape("dot", ((-3,-3), (-3,3), (3,3), (3,-3)))
screen.register_shape("tri", ((-3, -2), (0, 3), (3, -2), (0, 0)))
turtle.speed(0)



UPDATE_EVERY = 0
DRAW_EVERY = 2

class Map(object):
    """
    TODO: docstring
    """
    
    DEG_TO_RAD = math.pi / 180
    RAD_TO_DEG = 180 / math.pi
    
    def __init__(self, json_file):
        self.load_from_json_file(json_file)
        self.width, self.height = screen.screensize()


        # self.im_resized = self.im.resize((self.width, self.height),  Image.ANTIALIAS)

        self.photo = ImageTk.PhotoImage(self.im)
        # self.photo = self.photo.zoom(1000)
        canvas.create_image(0, 0, image=self.photo, anchor='nw')

        img_data = list(self.im.getdata())
        self.img_bitmap = np.zeros(len(img_data), dtype=np.int8)
        for i in np.arange(len(img_data)):
            if img_data[i] != (255, 255, 255):
                self.img_bitmap[i] = 1
        self.img_bitmap = self.img_bitmap.reshape(self.im.size[::-1])
        self.img_bitmap = self.img_bitmap.transpose()
        # print(screen.screensize())
        # print(self.im_pixels[468, 231], self.img_bitmap[468][231])
        # print(self.im.size)

        screen.setworldcoordinates(0, self.height - 1, self.width - 1, 0)
        turtle.home()
        # self.blocks = []
        self.update_cnt = 0
        self.one_px = float(turtle.window_width()) / float(self.width) / 2

        # self.beacons = []
        # for y, line in enumerate(self.maze):
        #     for x, block in enumerate(line):
        #         if block:
        #             nb_y = self.height - y - 1
        #             self.blocks.append((x, nb_y))
        #             if block == 2:
        #                 self.beacons.extend(((x, nb_y), (x+1, nb_y), 
        #                     (x, nb_y+1), (x+1, nb_y+1)))
    
    def load_from_json_file(self, json_file):
        json_data = open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), json_file))
        data = json.load(json_data)
        json_data.close()
        self.im = Image.open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), data["Filepath"]))
        self.im = self.im.convert('RGB')
        self.im_pixels = self.im.load()
        self.lats = [None] * 2
        self.lons = [None] * 2
        self.xs = [None] * 2
        self.ys = [None] * 2
        for i in range(0, 2):
            self.lats[i] = data["Points"][i]["GPS"]["latitude"]
            self.lons[i] = data["Points"][i]["GPS"]["longitude"]
            self.xs[i] = data["Points"][i]["Pixel world"]["x"]
            self.ys[i] = data["Points"][i]["Pixel world"]["y"]
    
        self.beacons = data["Beacons"]
        
        self.angle = self.getAngle()
        self.metersForPixel = self.calculateMetersForPixel()

        (x, y) = self.PixelsToXYMeters(self.xs[1], self.ys[1])
        self.origin = self.XYMetersToGPS(
            self.lats[1], self.lons[1], -x, -y)    
  
    def check(self, x0, y0):
        if not self.is_in(x0, y0):
            return False
        self.im_pixels[int(x0), int(y0)] = (0, 0, 255)
        return self.img_bitmap[int(x0)][int(y0)] == 0

    def segment_is_intersecting_walls(self, x0, y0, x1, y1):
       
       # print('*')
       # for i in range(100):
       #     for j in range(100):
       #         self.im_pixels[i, j] = (0, 255, 0)

       x0 = int(x0)
       y0 = int(y0)
       x1 = int(x1)
       y1 = int(y1)

       dx = abs(x1-x0)
       dy = abs(y1-y0) 
       if (x0 < x1):
           sx = 1
       else:
           sx = -1
       if (y0 < y1):
           sy = 1
       else:
           sy = -1
       err = dx-dy
     
       while(True):
         # print x0, y0
         if(not self.check(x0,y0)):
             # print 0
             return True
         if (x0 == x1 and y0 == y1):
             break
         e2 = 2*err
         if (e2 > -dy): 
           err = err - dy
           x0 = x0 + sx
         if (x0 == x1 and y0 == y1):
           if(not self.check(x0,y0)):
               # print 0
               return True
           break
         if (e2 <  dx):
           err = err + dx
           y0 = y0 + sy
       return False



    def GPSToXYMeters(self, latitude1, longitude1, latitude2, longitude2):
        x = (longitude1 - longitude2) * self.DEG_TO_RAD * math.cos((latitude1 + latitude2) * self.DEG_TO_RAD/2) * 6371000
        y = (latitude1 - latitude2) * self.DEG_TO_RAD * 6371000
        xnew = x * math.cos(-self.angle) - y * math.sin(-self.angle)
        ynew = x * math.sin(-self.angle) + y * math.cos(-self.angle)
        return (xnew, -ynew)

    def GPSToAbsoluteXYMeters(self, latitude, longitude):
        return self.GPSToXYMeters(latitude, longitude, self.origin[0], self.origin[1])

    def XYMetersToGPS(self, latitude1, longitude1, x, y):
        xnew = x * math.cos(self.angle) + y * math.sin(self.angle)
        ynew = x * math.sin(self.angle) - y * math.cos(self.angle)
        bearing = math.atan2(xnew, ynew)
        d = math.sqrt(xnew * xnew + ynew * ynew)
        latitude = math.asin(math.sin(latitude1 * self.DEG_TO_RAD) * math.cos(d/6371000) + math.cos(latitude1 * self.DEG_TO_RAD) * math.sin(d/6371000) * math.cos(bearing)) * self.RAD_TO_DEG
        longitude = longitude1 + math.atan2(math.sin(bearing) * math.sin(d/6371000) * math.cos(latitude1 * self.DEG_TO_RAD), math.cos(d/6371000) - math.sin(latitude1 * self.DEG_TO_RAD) * math.sin(latitude * self.DEG_TO_RAD)) * self.RAD_TO_DEG
        return (latitude, longitude)

    def AbsoluteXYMetersToGPS(self, x, y):
        return self.XYMetersToGPS(self.origin[0], self.origin[1], x, y)

    def XYMetersToPixels(self, x, y):
        return (x / self.metersForPixel[0], y / self.metersForPixel[1])

    def PixelsToXYMeters(self, px, py):
        return (px * self.metersForPixel[0], py * self.metersForPixel[1])

    def calculateMetersForPixel(self):
        (x, y) = self.GPSToXYMeters(self.lats[0], self.lons[0], self.lats[1], self.lons[1])
        (px, py) = (self.xs[0] - self.xs[1], self.ys[0] - self.ys[1])
        return (math.fabs(x/px), math.fabs(y/py))

    def getAngle(self):
        if(self.xs[1]>self.xs[0]):
            x = (self.lons[1] - self.lons[0]) * self.DEG_TO_RAD * math.cos((self.lats[1] + self.lats[0]) * self.DEG_TO_RAD/2) * 6371000
            y = (self.lats[1] - self.lats[0]) * self.DEG_TO_RAD * 6371000
            angle1 = math.atan2(y, x)
            angle2 = math.atan2(-self.ys[1] + self.ys[0], self.xs[1] - self.xs[0])
        else:
            x = (self.lons[0] - self.lons[1]) * self.DEG_TO_RAD * math.cos((self.lats[0] + self.lats[1]) * self.DEG_TO_RAD/2) * 6371000
            y = (self.lats[0] - self.lats[1]) * self.DEG_TO_RAD * 6371000
            angle1 = math.atan2(y, x)
            angle2 = math.atan2(-self.ys[0] + self.ys[1], self.xs[0] - self.xs[1])
        return angle1 - angle2	   

    def draw(self):
        screen.update()
        
    def weight_to_color(self, weight):
        return "#%02x00%02x" % (int(weight * 255), int((1 - weight) * 255))

    def is_in(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        return True

    def is_free(self, x, y):
        if not self.is_in(x, y):
            return False

        # print(x, y,  self.img_bitmap[int(x)][int(y)])
        return self.img_bitmap[int(x)][int(y)] == 0

    def show_mean(self, x, y, confident=False):
        if not hasattr(self, 'mean_pos_id'):
            self.mean_pos_id = canvas.create_oval(x-3, y-3, x+3, y+3, 
                fill='green', outline='green')
        canvas.coords(self.mean_pos_id, x-3, y-3, x+3, y+3)
        canvas.update()
        
    def show_particles(self, particles):
        self.update_cnt += 1
        if UPDATE_EVERY > 0 and self.update_cnt % UPDATE_EVERY != 1:
            return

        for p in particles:
            if not hasattr(p, 'canvas_id'):
                p.canvas_id = canvas.create_rectangle(p.x, p.y,
                    p.x, p.y, fill="blue", outline="blue")
            canvas.coords(p.canvas_id, p.x, p.y, p.x, p.y)

        canvas.update()

    def show_robot(self, robot):
        if not hasattr(robot, 'canvas_id'):
            print(robot.x, robot.y)
            robot.canvas_id = canvas.create_oval(robot.x-2, robot.y-2,
                robot.x+2, robot.y+2, fill="red", outline="red")
        canvas.coords(robot.canvas_id,
            robot.x-2, robot.y-2, robot.x+2, robot.y+2)
        
        # print(canvas.coords(robot.canvas_id))

        # print(canvas.bbox(robot.canvas_id))
        # canvas.coords(robot.canvas_id, (robot.x, robot.y))
        # print("Show robot", x, y)
        # turtle.color("green")
        # turtle.shape('turtle')
        # turtle.up()
        # turtle.setposition(x, y)
        # turtle.setheading(h)
        # turtle.down()
        # turtle.clearstamps()
        # turtle.stamp()
        # turtle.dot()
        canvas.update()


    def random_place(self):
        x = random.uniform(0, self.width - 1)
        y = random.uniform(0, self.height - 1)
        return x, y

    def random_free_place(self):
        while True:
            x, y = self.random_place()
            if self.is_free(x, y):
                return x, y

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def distance_to_nearest_beacon(self, x, y):
        d = 99999
        for b in self.beacons:
            bx = b["Pixel world"]["x"]
            by = b["Pixel world"]["y"]
            distance = self.distance(bx, by, x, y)
            if distance < d:
                d = distance

        return d
        # return 0.1

    def distance_array_to_beacons(self, x, y):
        distance_array = []
        for b in self.beacons:
            bx = b["Pixel world"]["x"]
            by = b["Pixel world"]["y"]
            distance = self.distance(bx, by, x, y)
            distance_array.append(distance)
        return distance_array

def main():
    dfki_map = Map('dfki-2nd-floor.json')
    

    # canvas = screen.getcanvas()
    # rect = canvas.create_rectangle(0, 0, 999, 0, fill="blue")

    # print(screen.screensize())

    print(dfki_map.im.getpixel((1000, 350)))

    # 
    print(dfki_map.img_bitmap.shape)

    dfki_map.draw()


    # for i in range(0, 100, 10):
        # dfki_map.show_robot(i, 10, i)
        # canvas.move(rect, i, 2*i)
        # screen.update()
        # canvas.update_idletasks()
        # time.sleep(1)

if __name__ == '__main__':
    main()