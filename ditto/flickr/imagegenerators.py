from imagekit import ImageSpec, register
from imagekit.processors import Adjust, ResizeToFill, ResizeToFit, Transpose


# Info about different Flickr image sizes:
# https://www.flickr.com/services/api/misc.urls.html
#
# Also see ditto.flickr.models.Photo


# BASE CLASSES

class FlickrSpec(ImageSpec):
    "Base class for most specs. Keeps same proportions."
    format = 'JPEG'
    options = {'quality': 80}
    # If original image is smaller, don't enlarge it:
    upscale = False

    def __init__(self, source):
        self.processors = [
                Transpose(),
                ResizeToFit(self.width, self.height, upscale=self.upscale),
                Adjust(sharpness=2.0),]
        super().__init__(source)


class FlickrSquareSpec(ImageSpec):
    "Base class for the square specs. Crops to a square."
    format = 'JPEG'
    options = {'quality': 70}
    # If original image is smaller, enlarge it to fill:
    upscale = True

    def __init__(self, source):
        self.processors = [
                Transpose(),
                ResizeToFill(self.size, self.size, upscale=self.upscale),
                Adjust(sharpness=2.0),]
        super().__init__(source)


# SQUARES

class Square(FlickrSquareSpec):
    size = 75
register.generator('ditto_flickr:square', Square)

class LargeSquare(FlickrSquareSpec):
    size = 150
register.generator('ditto_flickr:large_square', LargeSquare)


# NATURAL PROPORTIONS

class Thumbnail(FlickrSpec):
    width = 100
    height = 100
    # If original image is smaller, enlarge it to fit:
    upscale = True
register.generator('ditto_flickr:thumbnail', Thumbnail)

class Small(FlickrSpec):
    width = 240
    height = 240
register.generator('ditto_flickr:small', Small)

class Small320(FlickrSpec):
    width = 320
    height = 320
register.generator('ditto_flickr:small_320', Small320)

class Medium(FlickrSpec):
    width = 500
    height = 500
register.generator('ditto_flickr:medium', Medium)

class Medium640(FlickrSpec):
    width = 640
    height = 640
register.generator('ditto_flickr:medium_640', Medium640)

class Medium800(FlickrSpec):
    width = 800
    height = 800
register.generator('ditto_flickr:medium_800', Medium800)

class Large(FlickrSpec):
    width = 1024
    height = 1024
register.generator('ditto_flickr:large', Large)

class Large1600(FlickrSpec):
    width = 1600
    height = 1600
register.generator('ditto_flickr:large_1600', Large1600)

class Large2048(FlickrSpec):
    width = 2048
    height = 2048
register.generator('ditto_flickr:large_2048', Large2048)

