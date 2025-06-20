from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os

def validate_image(image):
    ext = os.path.splitext(image.name)[1][1:].lower()
    if ext not in ['jpeg', 'jpg', 'png', 'gif']:
        raise ValidationError(_('Недопустимый формат изображения.'))
    if image.size > 2 * 1024 * 1024:
        raise ValidationError(_('Размер изображения не должен превышать 2MB.'))
