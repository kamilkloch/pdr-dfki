import couchdb
from gps import Converter
import Image
import os
import ImageDraw
import webbrowser
import threading
from datetime import datetime
from dateutil.relativedelta import relativedelta

def sync(start, end):
    print __file__
    global draw
    update = 0
    for row in all_location_documents_from_elvis[ [start] : [end] ]:
        update = 1
        doc = db[row.id]
        meters = c.GPSToAbsoluteXYMeters(doc['location']['positions'][-1]['latitude'], doc['location']['positions'][-1]['longitude'])
        px = c.XYMetersToPixels(meters[0], meters[1])
        if(0<px[0]<im.size[0] and 0<px[1]<im.size[1]):
            if(row['key'][1] == '78:6C:1C:CD:16:8D'):
                fill = "#11FFFF"
            else:
                fill = "#FF00FF"
            ImageDraw.Draw(rgb_im).rectangle([(px[0]-5, px[1]-5), (px[0]+5, px[1]+5)], fill=fill)
    if(update):
        rgb_im.save(os.path.dirname(os.path.abspath(__file__)) +"/result.png")
        webbrowser.get('safari').open_new_tab("file://" + os.path.dirname(os.path.abspath(__file__)) + "/result.png")
    date_object = datetime.strptime(end, '%Y-%m-%d') + relativedelta(days=1)
    threading.Timer(1, sync, [end, date_object.strftime('%Y-%m-%d')]).start()


im = Image.open(os.path.dirname(os.path.abspath(__file__)) + "/dfki-2.png")
rgb_im = im.convert('RGB')
draw = ImageDraw.Draw(rgb_im)

couch = couchdb.Server('http://dfki-1239.dfki.uni-kl.de:5984/')
db = couch['ble']

all_location_documents_from_elvis = db.view("_design/elvis/_view/all_location_documents_from_elvis/",None)
c = Converter("json.json")
sync('2013-08-10', '2013-08-11')