import couchdb
from gps import Converter
import Image, copy
from images2gif import writeGif
import os, inspect
import ImageDraw
import webbrowser
from bs4 import BeautifulSoup
import threading
from datetime import datetime
from dateutil.relativedelta import relativedelta

def sync(end, start, delta, drawPath):
    im = Image.open("./dfki-2.png")
    rgb_im = im.convert("RGB")
    im2 = Image.open("./dfki-2.png")
    rgb_im2 = im2.convert("RGB")
    if(drawPath):
        draw = ImageDraw.Draw(rgb_im)

        prvx = [None] * 10
        prvy = [None] * 10
        

        fill = [None] * 10
        fill[0] = (170, 0, 0)
        fill[1] = (21, 94, 235)
        fill[2] = (0, 170, 0)

    count = 0
    devices = [None] * 10
    gifs = [None] * 10
    gifs[0] = "./red.gif"
    gifs[1] = "./blue.gif"
    gifs[2] = "./green.gif"

    pngs = [None] * 10
    pngs[0] = "./red dot.png"
    pngs[1] = "./blue dot.png"
    pngs[2] = "./green dot.png"

    animate = [None] * 10
    animate[0] = 0
    animate[1] = 0
    animate[2] = 0
    
    soup = BeautifulSoup(open("html.html"))
    images = soup.html.body.find("div", {"id": "images"})
    images.clear()
    for row in all_location_documents_from_elvis[ [(end + relativedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S') ] : [start.strftime('%Y-%m-%d %H:%M:%S')] ]:
        doc = db[row.id]
        for position in reversed(doc['location']['positions']):
            if(start < datetime.strptime(position['timestamp'][:-4], '%Y-%m-%d %H:%M:%S') < end):
                meters = c.GPSToAbsoluteXYMeters(position['latitude'], position['longitude'])
                px = c.XYMetersToPixels(meters[0], meters[1])
                if(0 < px[0] < im.size[0] and 0 < px[1] < im.size[1]):
                    found = 0
                    i = 0
                    while i < count:
                        if(row['key'][1] == devices[i]):
                            found = 1
                            break
                        i +=1
                    if(found):
                        if(not animate[i]):
                            animate[i] = 1;
                            latest = soup.find("img", {"class": "latest", "id": devices[i]})
                            latest['style'] = "position:absolute;top:"+str(px[1]-100)+"px;left:"+str(px[0]-100)+"px;z-index:10;"
                        else:
                            if(drawPath):
                                img = soup.new_tag("img", src=pngs[i], style="position:absolute;top:"+str(px[1]-12)+"px;left:"+str(px[0]-12)+"px;z-index:10;")
                                images.append(img)
                                draw.line((px[0],px[1], prvx[i],prvy[i]), fill=fill[i], width=2)
                    else :
                        #left = int(px[0])-300
                        #top = int(px[1])-200
                        #width = 600
                        #height = 400
                        #box = (left, top, left+width, top+height)
                        #area = rgb_im2.crop(box)
                        #ball = Image.open("./red dot.png")
                        #rgb_ball = ball.convert("RGB")
                        #area.paste(rgb_ball, (288,188))
                        #filelist = [ f for f in os.listdir("../mirror-quickstart-java-master/src/main/webapp/static/maps/")]
                        #for f in filelist:
                        #    os.remove("../mirror-quickstart-java-master/src/main/webapp/static/maps/" + f)
                        #area.save('../mirror-quickstart-java-master/src/main/webapp/static/maps/result'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'.jpeg')
                        devices[count] = row['key'][1]
                        count += 1
                        date = datetime.strptime(row.key[0][:-4], '%Y-%m-%d %H:%M:%S')
                        #if(not datetime.now() -  delta < date < datetime.now()):
                        img = soup.new_tag("img", src=gifs[i], style = "position:absolute;top:"+str(px[1]-100)+"px;left:"+str(px[0]-100)+"px;z-index:10;")
                        img['class'] = 'latest'
                        img['title'] = str(px[0]-100)+','+str(px[1]-100)
                        if(drawPath):
                            img['title']+= ',<img src=\''+pngs[i]+'\''
                        img['id'] = devices[i]
                        images.append(img)
                    if(drawPath):
                        prvx[i] = px[0]
                        prvy[i] = px[1]
    rgb_im.save("./result.png")
    legend = soup.html.body.find("div", {"id": "legend"})
    legend.clear()
    ct = 0
    ul = soup.new_tag("ul")
    while ct < count:
        li = soup.new_tag("li")
        li.string = devices[ct]
        li.append(soup.new_tag("img", src = pngs[ct]))
        ul.append(li)
        ct +=1
    legend.append(ul)
    html = soup.prettify("utf-8")
    with open("html.html", "wb") as file:
        file.write(html)
    webbrowser.get('safari').open_new_tab("file://" + filepath + "/html.html")


def showHistory(end, start, step, drawPath, newStart):
    newStart = newStart + step
    sync(newStart , start, step, drawPath)
    if(newStart < end):
        threading.Timer(1, showHistory, [end, start, step, drawPath, newStart]).start()

def showLive(tailInterval, drawPath):
    start = datetime.now() - tailInterval - relativedelta(seconds = 1)
    sync(datetime.now() , start, tailInterval, drawPath)
    threading.Timer(1, showLive, [tailInterval, drawPath]).start()

filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory

couch = couchdb.Server('http://dfki-1239.dfki.uni-kl.de:5984/')
db = couch['ble']

all_location_documents_from_elvis = db.view("_design/elvis/_view/all_location_documents_from_elvis/", None, descending=True)
c = Converter("json.json")

#sync(datetime.strptime('2013-08-14 18:31:30', '%Y-%m-%d %H:%M:%S'), datetime.strptime('2013-08-10 18:30:00', '%Y-%m-%d %H:%M:%S'), relativedelta(days = 3), 0)
showHistory(datetime.strptime('2013-08-14 18:31:10', '%Y-%m-%d %H:%M:%S'), datetime.strptime('2013-08-14 18:30:06', '%Y-%m-%d %H:%M:%S'), relativedelta(seconds = 1), 0, datetime.strptime('2013-08-14 18:30:06', '%Y-%m-%d %H:%M:%S'))
#showLive(relativedelta(days = 30), 1)


