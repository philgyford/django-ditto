from imagekit import ImageSpec, register
from imagekit.processors import Adjust, ResizeToFill, ResizeToFit, Transpose


class TwitterSpec(ImageSpec):
    "Base class for Medium and Small specs."
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


# The 'Large' size appears to be the original image, so we're not using
# Imagekit to generate these.
#class Large(TwitterSpec):
    #pass
#
#register.generator('ditto_twitter:large', Large)


class Medium(TwitterSpec):
    width = 1200
    height = 1200

register.generator('ditto_twitter:medium', Medium)


class Small(TwitterSpec):
    width = 680
    height = 680

register.generator('ditto_twitter:small', Small)


class Thumbnail(ImageSpec):
    width = 150
    height = 150
    upscale = True

    def __init__(self, source):
        self.processors = [
                Transpose(),
                ResizeToFill(self.width, self.height, upscale=True),
                Adjust(sharpness=2.0),]
        super().__init__(source)

register.generator('ditto_twitter:thumbnail', Thumbnail)

