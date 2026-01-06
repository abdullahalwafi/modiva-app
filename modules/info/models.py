from django.db import models
from modules.uman.models import Menu,GroupMenu

from django.contrib.auth.models import User,Group
from libs.models import BaseAuditModel
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from modules.core.validators import validate_content_type_pdf
from modules.core.models import  OverwriteStorage

# Create your models here.
import uuid
import os

def get_file_pdf_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('info/file_pdf', filename)

