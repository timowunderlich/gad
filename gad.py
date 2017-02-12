import argparse
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup as bs
from PIL import Image
from io import BytesIO

def is_url(string):
    return urllib.parse.urlparse(string).scheme != ""

def get_image(url):
    print("Getting data from %s..." % url)
    with urllib.request.urlopen(url) as request:
        html_data = request.read()
    soup = bs(html_data, "html.parser")
    try:
        title = soup.find("meta", property="og:title")["content"]
        author, work = title.split(" - ")[0], title.split(" - ")[1]
        imageurl = soup.find("meta", property="og:image")["content"]
    except KeyError:
        print("Could not relevant data in HTML. Page changed?")
        return -1
    print("Found data for %s by %s, finding maximum zoom level..." % (author, work))
    zoomlevel = 0
    failed = False
    print(imageurl)
    while not failed:
        try:
            urllib.request.urlopen('%s=x0-y0-z%d' % (imageurl, zoomlevel))
        except:
            failed = True
            zoomlevel -= 1
        else:
            zoomlevel += 1
    print("Found maximum zoom level %d, getting partial images along vertical dimension..." % zoomlevel)
    partials = []
    y = 0
    failed = False
    while not failed:
        try:
            partial_request = urllib.request.urlopen('%s=x0-y%d-z%d' % (imageurl, y, zoomlevel))
        except:
            failed = True
            ymax = y
        else:
            partial = partial_request.read()
            partial = Image.open(BytesIO(partial))
            partials.append([partial])
            y += 1
    print("Found vertical extent of %d partial images, getting partial images along horizontal dimension..." % (ymax))
    x = 1 
    xmax = 0
    y = 0
    failed = False
    while not failed:
        try:
            if y == ymax:
                break
            partial_request =  urllib.request.urlopen('%s=x%d-y%d-z%d' % (imageurl, x, y, zoomlevel))
        except:
            if y < ymax:
                xmax, x = x, 1 # get next row of partial images
                y += 1
            else:
                failed = True # got all rows
        else:
            partial = partial_request.read()
            partial = Image.open(BytesIO(partial))
            partials[y].append(partial)
            x += 1
    print("Found horizontal extent of %d partial images. Stitching images together..." % (xmax))
    partial_xlen = partials[0][0].size[0]
    partial_ylen = partials[0][0].size[1]
    whole_image = Image.new("RGB", (partial_xlen*xmax, partial_ylen*ymax))
    for y, x_partials in enumerate(partials):
        for x, partial in enumerate(x_partials):
            whole_image.paste(partial, (x*partial_xlen, y*partial_ylen))
    whole_image = whole_image.crop(whole_image.getbbox()) # crop out empty parts
    print("Stitched images together, total resolution %dx%d. Saving image." % (whole_image.size[0], whole_image.size[1]))
    whole_image.save("%s - %s.jpg" % (author, work), quality=100)


parser = argparse.ArgumentParser(description="Download given artwork from Google Arts & Culture URL (highest resolution available).")
parser.add_argument("source", metavar="URL/Filename", type=str, help="Google Arts & Culture URL or filename of list of URLs.")
args = parser.parse_args()

if is_url(args.source):
    print("URL provided.")
    get_image(args.source)
else:
    with open(args.source, "r") as file:
        urls = [line.rstrip("\n") for line in file]
    print("List of %d URLs provided." % len(urls))
    for url in urls:
        get_image(url)