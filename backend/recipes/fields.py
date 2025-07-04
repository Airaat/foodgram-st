from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as fmt
import os

MAX_SIZE = 2 * 1024 * 1024  # 2 Mb

UNSUPPORTED_FORMAT = 'Недопустимый формат изображения.'
UNSUPPORTED_IMAGE_SIZE = 'Размер изображения не должен превышать 2MB.'


def validate_image(image):
    ext = os.path.splitext(image.name)[1][1:].lower()

    if ext not in ['jpeg', 'jpg', 'png', 'gif']:
        raise ValidationError(fmt(UNSUPPORTED_FORMAT))

    if image.size > MAX_SIZE:
        raise ValidationError(fmt(UNSUPPORTED_IMAGE_SIZE))
