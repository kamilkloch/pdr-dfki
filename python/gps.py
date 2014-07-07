import Image
import os
import math
import json

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi


class Converter(object):
  
        #1
        def GPSToXYMeters(self, latitude1, longitude1, latitude2, longitude2):
            x = (longitude1 - longitude2) * deg_to_rad * math.cos((latitude1 + latitude2) * deg_to_rad/2) * 6371000
            y = (latitude1 - latitude2) * deg_to_rad * 6371000
            xnew = x * math.cos(-self.angle) - y * math.sin(-self.angle)
            ynew = x * math.sin(-self.angle) + y * math.cos(-self.angle)
            return (xnew, -ynew)
    
        def GPSToAbsoluteXYMeters(self, latitude, longitude):
            return self.GPSToXYMeters(latitude, longitude, self.origin[0], self.origin[1])

        #2
        def XYMetersToGPS(self, latitude1, longitude1, x, y):
            xnew = x * math.cos(self.angle) + y * math.sin(self.angle)
            ynew = x * math.sin(self.angle) - y * math.cos(self.angle)
            bearing = math.atan2(xnew, ynew)
            d = math.sqrt(xnew * xnew + ynew * ynew)
            latitude = math.asin(math.sin(latitude1 * deg_to_rad) * math.cos(d/6371000) + math.cos(latitude1 * deg_to_rad) * math.sin(d/6371000) * math.cos(bearing)) * rad_to_deg
            longitude = longitude1 + math.atan2(math.sin(bearing) * math.sin(d/6371000) * math.cos(latitude1 * deg_to_rad), math.cos(d/6371000) - math.sin(latitude1 * deg_to_rad) * math.sin(latitude * deg_to_rad)) * rad_to_deg
            return (latitude, longitude)
    
        def AbsoluteXYMetersToGPS(self, x, y):
            return self.XYMetersToGPS(self.origin[0], self.origin[1], x, y)

        #3    
        def XYMetersToPixels(self, x, y):
            return (x / self.metersForPixel[0], y / self.metersForPixel[1])

        #4   
        def PixelsToXYMeters(self, px, py):
            return (px * self.metersForPixel[0], py * self.metersForPixel[1])

        #5        
        def calculateMetersForPixel(self):
            (x, y) = self.GPSToXYMeters(self.lats[0], self.lons[0], self.lats[1], self.lons[1])
            (px, py) = (self.xs[0] - self.xs[1], self.ys[0] - self.ys[1])
            return (math.fabs(x/px), math.fabs(y/py))

        #6
        def getAngle(self):
            if(self.xs[1]>self.xs[0]):
                x = (self.lons[1] - self.lons[0]) * deg_to_rad * math.cos((self.lats[1] + self.lats[0]) * deg_to_rad/2) * 6371000
                y = (self.lats[1] - self.lats[0]) * deg_to_rad * 6371000
                angle1 = math.atan2(y, x)
                angle2 = math.atan2(-self.ys[1] + self.ys[0], self.xs[1] - self.xs[0])
            else:
                x = (self.lons[0] - self.lons[1]) * deg_to_rad * math.cos((self.lats[0] + self.lats[1]) * deg_to_rad/2) * 6371000
                y = (self.lats[0] - self.lats[1]) * deg_to_rad * 6371000
                angle1 = math.atan2(y, x)
                angle2 = math.atan2(-self.ys[0] + self.ys[1], self.xs[0] - self.xs[1])
            return angle1 - angle2
            
          # the class constructor
        def __init__(self, jsonFile):
            json_data = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), jsonFile))
            data = json.load(json_data)
            json_data.close()
            self.im = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), data["Filepath"]))
            self.lats = [None] * 2
            self.lons = [None] * 2
            self.xs = [None] * 2
            self.ys = [None] * 2
            for i in range(0, 2):
       	        self.lats[i] = data["Points"][i]["GPS"]["latitude"]
                self.lons[i] = data["Points"][i]["GPS"]["longitude"]
                self.xs[i] = data["Points"][i]["Pixel world"]["x"]
                self.ys[i] = data["Points"][i]["Pixel world"]["y"]
        
            self.angle = self.getAngle()
            self.metersForPixel = self.calculateMetersForPixel()

            (x, y) = self.PixelsToXYMeters(self.xs[1], self.ys[1])
            self.origin = self.XYMetersToGPS(self.lats[1], self.lons[1], -x, -y)