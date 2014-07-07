""" MODULE images2gif
 
Provides a function (writeGif) to write animated gif from a series
of PIL images
 
This code is provided as is, and is free to use for all.
 
Almar Klein (June 2009)
Will Pierce (March 2013) - removed numpy support and refactored internals
 
- based on gifmaker (in the scripts folder of the source distribution of PIL)
- based on gif file structure as provided by wikipedia
"""
 
import struct
import PIL
from PIL import Image
from PIL.GifImagePlugin import getheader, getdata
 
# getheader gives a 87a header and a color palette (two elements in a list).
# getdata()[0] gives the Image Descriptor up to (including) "LZW min code size".
# getdatas()[1:] is the image data itself in chuncks of 256 bytes (well
# technically the first byte says how many bytes follow, after which that
# amount (max 255) follows).
 
intToBin = struct.Struct('<H').pack
 
def getheaderAnim(im):
  """ Animation header. To replace the getheader()[0] """
  return ''.join(["GIF89a",
                  intToBin(im.size[0]),
                  intToBin(im.size[1]),
                  "\x87\x00\x00"])
 
def getAppExt(loops):
  """ Application extention. Part that secifies amount of loops.
 if loops is 0, it goes on infinitely.
 """
  return ''.join(["\x21\xFF\x0B",  # application extension
                  "NETSCAPE2.0",
                  "\x03\x01",
                  intToBin(loops),
                  '\x00'])  # end
 
def getGraphicsControlExt(duration=0.1):
  """ Graphics Control Extension. A header at the start of
 each image. Specifies transparancy and duration. """
  return ''.join(['\x21\xF9\x04',
                  '\x08',  # no transparency
                  intToBin(int(duration * 100)), # in 100th of seconds
                  '\x00',  # no transparent color
                  '\x00'])  # end
 
def _writeGifToFile(fp, images, durations, loops):
  """ Given a set of images writes the bytes to the specified stream."""
  # first image, gather data for global header
  img = images[0]
  header = getheaderAnim(img)
  palette = getheader(img)[1]
  appext = getAppExt(loops)
 
  # output the initial header
  fp.write(header)
  fp.write(palette)
  fp.write(appext)
 
  # write sequence of images
  for img, duration in zip(images, durations):
    graphext = getGraphicsControlExt(duration)
    fp.write(graphext)
    for dat in getdata(img):
      fp.write(dat)
  fp.write(';')  # end gif marker
 
def writeGif(filename, images, duration=0.1, loops=0, dither=1):
    """Write an animated gif from the specified images.
   
   @param str filename - output filename
   @param list images - a list of PIL Images
   @param int/list duration - either a float for per-frame delay, or list of floats
   @param int loops - number of times the animation should loop, None means infinite
   @param int dither - dithering mode for Image.convert(), set to 0 to disable dithering
   """
    # build duration list
    try:
      assert len(duration) == len(images)
      durations = duration
    except TypeError:
      durations = [duration] * len(images)
     
    # convert to PIL gifs (palette mode)
    gifs = [img.convert('P', dither=dither) for img in images]
 
    with open(filename, 'wb') as fp:
      _writeGifToFile(fp, gifs, durations, loops)