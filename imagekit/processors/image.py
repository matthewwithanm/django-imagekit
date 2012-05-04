from ..lib import Image, ImageEnhance, ImageColor


class Watermark(object):
    """
    Processor for applying watermarks to images.

    """
    def __init__(self, image_path, style='scale', position=(0, 0), opacity=0.5):
        """
        :param bkgd_image_path: path to the watermark image.
        :param style: choices = tile, scale or position (where position is used)

        """
        self.image_path = image_path
        self.style = style
        self.position = position
        self.opacity = opacity

    def process(self, img):
        try:
            mark = Image.open(self.image_path)
        except IOError, e:
            raise IOError('Unable to open watermark source image %s: %s' % \
                          (self.image_path, e))
        # ensure RGBA mark:
        if mark.mode != 'RGBA':
            mark = mark.convert('RGBA')
        # change mark opacity if needed:
        if self.opacity >= 0 and self.opacity < 1:
            alpha = mark.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity)
            mark.putalpha(alpha)
        # add the mark:
        if self.style == 'tile':
            for y in range(0, img.size[1], mark.size[1]):
                for x in range(0, img.size[0], mark.size[0]):
                    img.paste(mark, (x, y), mark)
        elif self.style == 'scale':
            # scale, but preserve the aspect ratio
            ratio = min(
                float(img.size[0]) / mark.size[0], float(img.size[1]) / mark.size[1])
            if ratio != 1:
                w = int(mark.size[0] * ratio)
                h = int(mark.size[1] * ratio)
                mark = mark.resize((w, h))
                img.paste(mark, ((img.size[0] - w) / 2, (img.size[1] - h) / 2), mark)
            else:
                img.paste(mark, (0, 0), mark)
        else:
            img.paste(mark, self.position, mark)
        return img


class Frame(object):
    """
    Processor for applying watermarks to images.

    """
    def __init__(self, mark_image_path, mask_image_path=None, bkgd_image_path=None, bkgd_color='#FFFFFF'):
        """
        :param bkgd_image_path: path to the watermark image.

        """
        self.mark_image_path = mark_image_path
        self.mask_image_path = mask_image_path
        self.bkgd_image_path = bkgd_image_path
        self.bkgd_color = bkgd_color

    def process(self, img):
        try:
            if self.bkgd_image_path:
                bkgdim = Image.open(self.bkgd_image_path)
            else:
                if self.bkgd_color:
                    color = ImageColor.getrgb(self.bkgd_color)
                else:
                    color = 0
                bkgdim = Image.new("RGBA", (img.size[0], img.size[1]), color)
            markim = Image.open(self.mark_image_path)
            if self.mask_image_path:
                maskim = Image.open(self.mask_image_path)
            else:
                maskim = Image.new("RGBA", (img.size[0], img.size[1]))

        except IOError, e:
            raise IOError('Unable to open watermarks source images at %s: %s' % \
                          (self.image_path, e))

        # ensure RGBA mark:
        if markim.mode != 'RGBA':
            markim = markim.convert('RGBA')
        if maskim.mode != 'RGBA':
            maskim = maskim.convert('RGBA')

        img.paste(bkgdim, (0, 0), maskim)
        img.paste(markim, (0, 0), markim)

        return img
