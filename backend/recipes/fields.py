import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as fmt

from foodgram.settings import MAX_IMAGE_SIZE


UNSUPPORTED_FORMAT = 'Недопустимый формат изображения.'
UNSUPPORTED_IMAGE_SIZE = 'Размер изображения не должен превышать 2MB.'


def validate_image(image):
    ext = os.path.splitext(image.name)[1][1:].lower()

    if ext not in ['jpeg', 'jpg', 'png', 'gif']:
        raise ValidationError(fmt(UNSUPPORTED_FORMAT))

    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError(fmt(UNSUPPORTED_IMAGE_SIZE))
