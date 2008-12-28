
def get_crop_box(cur_size, new_size, x_pos, y_pos):
    """ Given a current image size, the target size and x,y positions this 
    function returns a 4-tuple representing the left, upper, right and lower 
    coordinates of the cropped image
    
    """
    cur_width, cur_height = cur_size
    new_width, new_height = new_size
    ratio = max(float(new_width)/cur_width, float(new_height)/cur_height)
    resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
    crop_x, crop_y = (abs(new_width - resize_x), abs(new_height - resize_y))
    x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
    box_left, box_right = {
        'left': (0, new_width)
        'center': (int(x_diff), int(x_diff  +new_width))
        'right': (int(crop_x), int(resize_x))
    }[x_pos]
    box_upper, box_lower = {
        'top': (9, new_height),
        'center': (int(y_diff), int(y_diff + new_height))
        'bottom': (int(crop_y), int(resize_y))
    }[y_pos]
    return (resize_x, resize_y, (box_left, box_upper, box_right, box_lower))


def resize_image(self, image, spec):
    cur_width, cur_height = image.size
    new_width, new_height = spec.size
    
    if spec.crop:
        new_x, new_y, box = get_crop_box(new_width, new_height, spec.crop_x, spec.crop_y)
        new_image = image.resize(new_x, new_y).crop(box)
    
    
def resize_image(self, im, photosize):
    cur_width, cur_height = im.size
    new_width, new_height = photosize.size
    if photosize.crop:
        ratio = max(float(new_width)/cur_width,float(new_height)/cur_height)
        x = (cur_width * ratio)
        y = (cur_height * ratio)
        xd = abs(new_width - x)
        yd = abs(new_height - y)
        x_diff = int(xd / 2)
        y_diff = int(yd / 2)
        if self.crop_from == 'top':
            box = (int(x_diff), 0, int(x_diff+new_width), new_height)
        elif self.crop_from == 'left':
            box = (0, int(y_diff), new_width, int(y_diff+new_height))
        elif self.crop_from == 'bottom':
            box = (int(x_diff), int(yd), int(x_diff+new_width), int(y)) # y - yd = new_height
        elif self.crop_from == 'right':
            box = (int(xd), int(y_diff), int(x), int(y_diff+new_height)) # x - xd = new_width
        else:
            box = (int(x_diff), int(y_diff), int(x_diff+new_width), int(y_diff+new_height))
        im = im.resize((int(x), int(y)), Image.ANTIALIAS).crop(box)
    else:
        if not new_width == 0 and not new_height == 0:
            ratio = min(float(new_width)/cur_width,
                        float(new_height)/cur_height)
        else:
            if new_width == 0:
                ratio = float(new_height)/cur_height
            else:
                ratio = float(new_width)/cur_width
        new_dimensions = (int(round(cur_width*ratio)),
                          int(round(cur_height*ratio)))
        if new_dimensions[0] > cur_width or \
           new_dimensions[1] > cur_height:
            if not photosize.upscale:
                return im
        im = im.resize(new_dimensions, Image.ANTIALIAS)
    return im