from django.core.exceptions import ValidationError
import pypdf 

def validate_file_size(value):
    print("#### SIZE : ",value.file.size)
    #SIZE = 10485760 #10 MB
    SIZE = 1048576 #1 MB
    if value.file.size > SIZE :
        raise ValidationError(u'File terlalu besar, maksimal : %s bytes.'%SIZE)

def validate_content_type_pdf(value):
    file_ = value.file
    try:
        pdf = pypdf.PdfReader(file_)
    except pypdf.errors.PdfStreamError:
        raise ValidationError(u'You must upload a valid PDF file')
