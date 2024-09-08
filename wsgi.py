import pymupdf, base64, gc
from urllib.parse import parse_qs

from PIL import Image
import io
from json import dumps as json_dumps

def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def application(environ, start_response):
    
    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    num_page = 0
    view_img = '2:1'
    format_pic = 'webp'
    output = dict()
    
    if request_body_size > 0:
        request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
        post_data = parse_qs(request_body)
        
        view_img = post_data.get('view_img')
        name_go = post_data.get('name_go')
        num_page = post_data.get('num_page')
                
        view_img = view_img[0] if view_img is not None else '-'
        name_go = name_go[0] if name_go is not None else '-'
        num_page = int(num_page[0]) if name_go is not None else 0
        
        if view_img == '2:2':
            int_num = 2
        else:
            int_num = 1
        
        if name_go == 'go_next':
            num_page += int_num
        elif name_go == 'go_prev':
            num_page -= int_num
        
    doc = pymupdf.open('big_maps.pdf')
    page_count = doc.page_count
    
    if (num_page > page_count - 1):
        num_page = 0
    if (num_page < 0):
        num_page = page_count - 1
    
    if (view_img != '1:1'):
        pix_1=doc[num_page-1].get_pixmap(dpi=150)
        pix_2=doc[num_page].get_pixmap(dpi=150)
        
        img_bytes_1 = pix_1.pil_tobytes(format=format_pic, optimize=False, quality = 72)
        input_image_1 = Image.open(io.BytesIO(img_bytes_1))
        
        img_bytes_2 = pix_2.pil_tobytes(format=format_pic, optimize=False, quality = 72)
        input_image_2 = Image.open(io.BytesIO(img_bytes_2))

        input_image = get_concat_h(input_image_1, input_image_2)
        img_bytes = io.BytesIO()
        input_image.save(img_bytes, format=format_pic, optimize = False, quality = 72)
        img_encoded = base64.b64encode(img_bytes.getvalue()).decode()
    else:
        pix=doc[num_page].get_pixmap(dpi=150)
        img_bytes = pix.pil_tobytes(format=format_pic, optimize=False, quality = 72)
        img_encoded = base64.b64encode(img_bytes).decode()
    
    output['page_count'] = page_count
    output['num_page'] = num_page
    output['view_img'] = view_img
    output['img_encoded'] = img_encoded
    img_encoded = json_dumps(output)
    img_encoded = img_encoded.encode()
    
    doc.close()
    
    status = '200 OK'

    response_headers = [('Content-type', 'text/json'), 
                        ('Cache-Control', 'no-store, no-cache'), 
                        ('Content-Length', str(len(img_encoded)))]
    start_response(status, response_headers)

    return [img_encoded]
    
gc.collect()
