from PIL import Image


def get_image_ratio(image: Image, w: int, h: int):
    image_x, image_y = image.size
    bbox_area = w * h
    image_area = image_x * image_y

    return bbox_area / image_area