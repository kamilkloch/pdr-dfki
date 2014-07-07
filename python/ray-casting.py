import Image
import os

def check(x0, y0):
    r, g, b = rgb_im.getpixel((x0, y0))
    pixels[x0,y0] = 22
    return r == 255 and g == 255 and b == 255

def isIntersectingWithWalls(x0, y0, x1, y1):
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
 
   while(1):
     print x0, y0
     if(not check(x0,y0)):
         print 0
         return 0
     if (x0 == x1 and y0 == y1):
         break
     e2 = 2*err
     if (e2 > -dy): 
       err = err - dy
       x0 = x0 + sx
     if (x0 == x1 and y0 == y1):
       if(not check(x0,y0)):
           print 0
           return 0
       break
     if (e2 <  dx):
       err = err + dx
       y0 = y0 + sy
   return 1 


im = Image.open(os.path.dirname(__file__) + "dfki-2.png")
rgb_im = im.convert('RGB')
pixels = rgb_im.load()
print isIntersectingWithWalls(210, 470, 210, 1000)

rgb_im.show()