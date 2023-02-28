# 필요한 module import
import os
import time
import glob

from PyPDF2 import PdfFileReader, PdfFileWriter
from pdfminer.layout import LAParams, LTTextLine, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

from pdf2image import convert_from_path, convert_from_bytes
from IPython.display import display
from PIL import Image, ImageDraw

#conver index(int) to str of specific size ex. 4 -> '0004' 
def index_convert_filename_regular_size(index, size):
    idx_len = len(str(index))
    filename = ''
    for _ in range(size-idx_len):
        filename += '0'
    filename += str(index)
    return filename    

# intial setting to progress PDF-_crop_function
def initialize(file_path):
    try:
        os.mkdir(file_path+'/pdf')
    except:
        print("already exist folder", file_path+'/pdf')
    try:
        os.mkdir(file_path+'/output')
    except:
        print("already exist folder", file_path+'/output')

    print('plz put in pdf files at '+ file_path +'/pdf')

    
    
#description-----------------------------------------------------    
#pdf_file : name of pdf file in pdf folder ex.'asd.pdf' 
#file_path : current dir path ex. os.getcwd()
#output_format : yolo(x_center, y_center, width, height, value), ocr(filename, value) 
#time_check(default False) : if you want to check time use this 
#save_crop_img(default True) : decide to save crop image 
#single_page : need update
def PDF_crop_function(pdf_file ,file_path = os.getcwd(), output_format = 'ocr',page_range = None, time_check = 0, save_crop_img = 1, save_label = 1, a = 0, print_option = False, draw_option = False):    
    if time_check ==1:
        start = time.time()
    #path setting
    pdf_path = file_path + '/pdf/' + pdf_file
    save_path = file_path +'/output/' + pdf_file[:pdf_file.rfind('.')]

    #make dir to save
    try:
        os.mkdir(save_path)
    except:
        print("already exist folder", save_path)
    #convert pdf to PIL image list
    try:
        #print("converting pdf to image...")
        img = convert_from_path(pdf_path)
        page_num = len(img)

        #print("getting pdf data ...")
        fp = open(pdf_path, 'rb')
        # pdf coordinate extraction 하기 위해서 필요한 변수 setting
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(detect_vertical = True)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = PDFPage.get_pages(fp)

        i = 0 # cnt for progress page
        check = 0 # ckeck for progress
        if page_range == None:
            page_range = range(page_num) 
        else:
            page_range = range(page_range[0], page_range[1]) 

        for page in pages:
            #pregress print
            if print_option ==True:
                if i/page_num > 0.25 and check == 0:
                    print('25% complete,', page_num-i, 'page is remain...')
                    check = 1
                elif i/page_num > 0.5 and check == 1:
                    print('50% complete,', page_num-i, 'page is remain...')
                    check = 2
                elif i/page_num > 0.75 and check == 2:
                    print('75% complete,', page_num-i, 'page is remain...')
                    check = 3

            #get data og the pdf page of i
            if  i in page_range: #only print single page
                x_max = page.mediabox[2]
                y_max =  page.mediabox[3]
                img_size = img[i].size
                page_path = save_path + '/' +index_convert_filename_regular_size(i, 4)
                try:
                    os.mkdir(page_path)
                except: 
                    #print("already exist folder", page_path)
                    pass

                interpreter.process_page(page)
                layout = device.get_result()
                with open(page_path +'/labels.txt', "w") as f:
                    j = 0
                    for obj in layout:
                        if isinstance(obj,LTTextBox):
                            for lobj in obj:
                                if isinstance(lobj,LTTextLine):
                                    x1, x2, y1, y2, value = lobj.bbox[0], lobj.bbox[2], lobj.bbox[1], lobj.bbox[3], lobj.get_text()
                                    #PIL coordinate transform
                                    #print('x1:', x1,'x2:', x2, 'y1:', y1,'y2:', y2, value)
                                    x1 = x1/(x_max)*img_size[0]
                                    x2 = x2/(x_max)*img_size[0]
                                    y1 = (1 - (y1/(y_max - a)))*img_size[1]
                                    y2 = (1 - (y2/(y_max - a)))*img_size[1]
                                    if draw_option == True:
                                        draw = ImageDraw.Draw(img[i])
                                        draw.rectangle([x1, y1,x2, y2], outline='yellow', width = 1)

                                    #write labeling data at txt. ex. bbox cordinate, value 
                                    if save_label == True:
                                        if output_format == 'yolo':
                                            x_center = (x1 + x2)/2
                                            y_center = (y2 + y1)/2
                                            width = x2-x1
                                            height = y1-y2
                                            f.write("0 %f %f %f %f %s" % (x_center, y_center, width, height, value))  
                                        elif output_format == 'ocr':
                                            f.write("%s\t%s" % (index_convert_filename_regular_size(j, 4)+'.jpg', value))  

                                    #save the crop image
                                    if save_crop_img == True:
                                        crop_img = img[i].crop((x1, y2, x2, y1))
                                        if 2*abs(x1-x2) < abs(y1-y2):
                                            crop_img = crop_img.rotate(90, expand=True)
                                        crop_img.save(page_path+ '/'+index_convert_filename_regular_size(j, 4)+'.jpg')
                                        if print_option ==True: display(crop_img)
                                        if print_option ==True: print(value)
                                    j += 1
                if print_option ==True: display(img[i])
            i += 1
        if time_check ==1:
            print(time.time()-start)
        #print('100% complete\r')
    except:
        pass
       