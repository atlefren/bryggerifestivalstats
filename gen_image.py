# -*- coding: utf-8 -*-

from gen_stats import Checkin, load_checkins
import bisect
from PIL import Image
import urllib
import cStringIO

WIDTH = 5616
HEIGHT = 3744


SIZES = {
    'photo_img_sm': 100,
    'photo_img_md': 320,
    'photo_img_lg': 640
}


def get_rowcol(img_size):
    cols = WIDTH / float(img_size)
    rows = HEIGHT / float(img_size)
    return (rows, cols)


def find_ut_size(req_size):
    idx = bisect.bisect(SIZES.values(), req_size)
    return SIZES.values()[idx]


def get_key(mlist, svalue):
    for key, value in mlist.items():
        if svalue == value:
            return key


def get_image(checkin, size):
    filename_size = get_key(SIZES, find_ut_size(size))
    filename = checkin.photos(filename_size)[0]
    image = Image.open(cStringIO.StringIO(urllib.urlopen(filename).read()))
    image = image.resize((size, size), Image.ANTIALIAS)
    return image

diff = 1000000
closest_size = None
if __name__ == '__main__':
    checkins = [Checkin(c) for c in load_checkins('run3.json')]
    checkins += [Checkin(c) for c in load_checkins('2015.json')]
    with_imgs = [c for c in checkins if c.has_media()]
    num_images = len(with_imgs)
    image_size = None
    for size in range(1, 640):
        rows, cols = get_rowcol(size)
        num = rows * cols
        new_diff = num_images - num
        if new_diff > 0 and new_diff < diff:
            diff = new_diff
            closest_size = size

        if num == num_images:
            image_size = size
            break
    if not image_size:
        image_size = closest_size

    rows, cols = get_rowcol(image_size)

    images = [get_image(c, image_size) for c in with_imgs]

    i = 0
    background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
    for col in range(0, int(cols)):
        for row in range(0, int(rows)):
            image = images[i]
            background.paste(image, (image_size * col, image_size * row))
            i += 1
    background.show()
    background.save("out2.jpg", "JPEG", quality=100, optimize=True)
