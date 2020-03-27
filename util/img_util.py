from django.core.files.images import ImageFile
from PIL import Image
from io import BytesIO


def scale_img(f, name, max_px, dim):
    try:
        img = Image.open(f, 'r')
    except IOError:
        raise ValueError('invalid image file')
    (w, h) = img.size
    if dim == 'h':
        if h > max_px:
            w = max_px * w / h
            h = max_px
        else:
            return f
    elif dim == 'both':
        if w > max_px or h > max_px:
            if w > h:
                h = max_px * h / w
                w = max_px
            else:
                w = max_px * w / h
                h = max_px
        else:
            return f

    scaled_img = img.resize((int(w),int(h)), Image.ANTIALIAS)
    scaled_buffer = BytesIO()
    scaled_img.save(scaled_buffer, 'PNG')
    scaled_f = ImageFile(scaled_buffer, name = name + '.png')
    return scaled_f
