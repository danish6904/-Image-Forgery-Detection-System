from importlib.resources import path
from tkinter import *
from tkinter import filedialog, ttk, messagebox
from optparse import OptionParser
from datetime import datetime
from matplotlib import image
from prettytable import PrettyTable
import numpy as np
import random
import sys
import cv2
import re
import os
from PIL import Image
from PIL import ImageTk
from PIL import ImageTk, Image, ExifTags, ImageChops
from pyparsing import Opt
from ForgeryDetection import Detect
import double_jpeg_compression
import noise_variance
import copy_move_cfa


IMG_WIDTH = 400
IMG_HEIGHT = 400
uploaded_image = None

cmd = OptionParser("usage: %prog image_file [options]")
cmd.add_option('', '--imauto',
               help='Automatically search identical regions. (default: %default)', default=1)
cmd.add_option('', '--imblev',
               help='Blur level for degrading image details. (default: %default)', default=8)
cmd.add_option('', '--impalred',
               help='Image palette reduction factor. (default: %default)', default=15)
cmd.add_option(
    '', '--rgsim', help='Region similarity threshold. (default: %default)', default=5)
cmd.add_option(
    '', '--rgsize', help='Region size threshold. (default: %default)', default=1.5)
cmd.add_option(
    '', '--blsim', help='Block similarity threshold. (default: %default)', default=200)
cmd.add_option('', '--blcoldev',
               help='Block color deviation threshold. (default: %default)', default=0.2)
cmd.add_option(
    '', '--blint', help='Block intersection threshold. (default: %default)', default=0.2)
opt, args = cmd.parse_args()

def getImage(path, width, height):
    """
    Function to return an image as a PhotoImage object
    :param path: A string representing the path of the image file
    :param width: The width of the image to resize to
    :param height: The height of the image to resize to
    :return: The image represented as a PhotoImage object
    """
    img = Image.open(path)
    img = img.resize((width, height), Image.LANCZOS)

    return ImageTk.PhotoImage(img)


def browseFile():
    """
    Function to open a browser for users to select an image
    :return: None
    """
    filename = filedialog.askopenfilename(title="Select an image", filetypes=[("image", ".jpeg"),("image", ".png"),("image", ".jpg")])

    if filename == "":
        return

    global uploaded_image

    uploaded_image = filename

    progressBar['value'] = 0
    fileLabel.configure(text=filename)

    img = Image.open(filename)
    img.thumbnail((400, 400))
    img = ImageTk.PhotoImage(img)
    img = getImage(filename, IMG_WIDTH, IMG_HEIGHT)
    imagePanel.configure(image=img)
    imagePanel.image = img

    blank_img = Image.new('RGB', (400, 400), color='white')
    blank_img = ImageTk.PhotoImage(blank_img)
    blank_img = getImage("images/output.png", IMG_WIDTH, IMG_HEIGHT)
    resultPanel.configure(image=blank_img)
    resultPanel.image = blank_img

    resultLabel.configure(text="READY TO SCAN", foreground="green")


def copy_move_forgery():
    path = uploaded_image
    eps = 60
    min_samples = 2

    if path is None:
        messagebox.showerror('Error', "Please select image")
        return

    detect = Detect(path)
    key_points, descriptors = detect.siftDetector()
    forgery = detect.locateForgery(eps, min_samples)

    progressBar['value'] = 100

    if forgery is None:
        img = getImage("images/no_copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img

        resultLabel.configure(text="ORIGINAL IMAGE", foreground="green")
    else:
        img = getImage("images/copy_move.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img

        resultLabel.configure(text="Image Forged", foreground="red")
        cv2.imshow('Forgery', forgery)
        wait_time = 1000
        while(cv2.getWindowProperty('Forgery', 0) >= 0) or (cv2.getWindowProperty('Original image', 0) >= 0):
            keyCode = cv2.waitKey(wait_time)
            if (keyCode) == ord('q') or keyCode == ord('Q'):
                cv2.destroyAllWindows()
                break
            elif keyCode == ord('s') or keyCode == ord('S'):
                name = re.findall(r'(.+?)(\.[^.]*$|$)', path)
                date = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')
                new_file_name = name[0][0]+'_'+str(eps)+'_'+str(min_samples)
                new_file_name = new_file_name+'_'+date+name[0][1]

                vaue = cv2.imwrite(new_file_name, forgery)
                print('Image Saved as....', new_file_name)


def metadata_analysis():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return

    img = Image.open(path)
    img_exif = img.getexif()

    progressBar['value'] = 100

    if img_exif is None:
        img = getImage("images/no_metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img

        resultLabel.configure(text="NO Data Found", foreground="red")
    else:
        img = getImage("images/metadata.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img

        resultLabel.configure(text="Metadata Details", foreground="green")

        with open('Metadata_analysis.txt', 'w') as f:
            for key, val in img_exif.items():
                if key in ExifTags.TAGS:
                        f.write(f'{ExifTags.TAGS[key]} : {val}\n')
        os.startfile('Metadata_analysis.txt')



def noise_variance_inconsistency():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    noise_forgery = noise_variance.detect(path)
    progressBar['value'] = 100

    if(noise_forgery):
        img = getImage("images/varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Noise variance", foreground="red")
    else:
        img = getImage("images/no_varience.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="No Noise variance", foreground="green")

def cfa_artifact():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    identical_regions_cfa = copy_move_cfa.detect(path, opt, args)
    progressBar['value'] = 100
    if(identical_regions_cfa):
        img = getImage("images/cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text=f"{str(identical_regions_cfa)}, CFA artifacts detected", foreground="red")
    else:
        img = getImage("images/no_cfa.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="NO-CFA artifacts detected", foreground="green")


def ela_analysis():
    path = uploaded_image
    TEMP = 'temp.jpg'
    SCALE = 10
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    original = Image.open(path)
    original.save(TEMP, quality=90)
    temporary = Image.open(TEMP)
    diff = ImageChops.difference(original, temporary)
    d = diff.load()
    WIDTH, HEIGHT = diff.size
    for x in range(WIDTH):
        for y in range(HEIGHT):
            d[x, y] = tuple(k * SCALE for k in d[x, y])
    progressBar['value'] = 100
    diff.show()



def jpeg_Compression():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    double_compressed = double_jpeg_compression.detect(path)
    progressBar['value'] = 100

    if(double_compressed):
        img = getImage("images/double_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Double compression", foreground="red")

    else:
        img = getImage("images/single_compression.png", IMG_WIDTH, IMG_HEIGHT)
        resultPanel.configure(image=img)
        resultPanel.image = img
        resultLabel.configure(text="Single compression", foreground="green")
        
def image_decode():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    img = cv2.imread(path) 
    width = img.shape[0]
    height = img.shape[1]
    img1 = np.zeros((width, height, 3), np.uint8)
    img2 = np.zeros((width, height, 3), np.uint8)
    for i in range(width):
        for j in range(height):
            for l in range(3):
                v1 = format(img[i][j][l], '08b')
                v2 = v1[:4] + chr(random.randint(0, 1)+48) * 4
                v3 = v1[4:] + chr(random.randint(0, 1)+48) * 4
                img1[i][j][l]= int(v2, 2)
                img2[i][j][l]= int(v3, 2)
        progressBar['value'] = 100
    cv2.imwrite('output.png', img2)
    im = Image.open('output.png')
    im.show()

def string_analysis():
    path = uploaded_image
    if path is None:
        messagebox.showerror('Error', "Please select image")
        return
    
    x=PrettyTable()
    x.field_names = ["Bytes", "8-bit", "string"]
    with open(path, "rb") as f:
            n = 0
            b = f.read(16)

            while b:
                s1 = " ".join([f"{i:02x}" for i in b]) 
                s1 = s1[0:23] + " " + s1[23:]
                s2 = "".join([chr(i) if 32 <= i <= 127 else "." for i in b])
                x.add_row([f"{n * 16:08x}",f"{s1:<48}",f"{s2}"])
                n += 1
                b = f.read(16)
            progressBar['value'] = 100

            with open('hex_viewer.txt', 'w') as w:
                w.write(str(x))
            os.startfile('hex_viewer.txt')
  
root = Tk()
root.title("IMAGE FORGERY DETECTION SYSTEM ")
root.iconbitmap('images/favicon.ico')

window_width = 1400
root.state('zoomed')
root.configure(bg='white')

root.protocol("WM_DELETE_WINDOW", root.quit)

root.state("zoomed")

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=5)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=36)
root.grid_columnconfigure(2, weight=3)
root.grid_columnconfigure(3, weight=1)
root.grid_columnconfigure(4, weight=1)

resultLabel = Label(text="INPUT IMAGE TO START", bg='white',font=("Leelawadee UI", 30))
resultLabel.grid(row=20, column=0, columnspan=3)

blank_img = Image.new('RGB', (400, 400), color='white')
blank_img = ImageTk.PhotoImage(blank_img)
input_img = getImage("images/input.png", IMG_WIDTH, IMG_HEIGHT)
middle_img = getImage("images/middle.png", IMG_WIDTH, IMG_HEIGHT)
output_img = getImage("images/output.png", IMG_WIDTH, IMG_HEIGHT)

imagePanel = Label(image=input_img)
imagePanel.image = input_img
imagePanel.grid(row=3, column=0, padx=5)

middle = Label(image=middle_img)
middle.image = middle_img
middle.grid(row=3, column=1, padx=5)

resultPanel = Label(image=output_img)
resultPanel.image = output_img
resultPanel.grid(row=3, column=2, padx=5)

fileLabel = Label(text="No file selected", fg="black", font=("Leelawadee UI", 15))
fileLabel.grid(row=4, column=1)

progressBar = ttk.Progressbar(length=500)
progressBar.grid(row=5, column=1)

s = ttk.Style()
s.configure('my.TButton', font=('Leelawadee UI', 10))

uploadButton = ttk.Button(
    text="Upload Image", style="my.TButton", command=browseFile)
uploadButton.grid(row=6, column=1, sticky="nsew", pady=10)

compression = ttk.Button(text="Compression-Detection",
                         style="my.TButton", command=jpeg_Compression)
compression.grid(row=7, column=0, columnspan=1, pady=20)

metadata = ttk.Button(text="Metadata-Analysis",
                      style="my.TButton", command=metadata_analysis)
metadata.grid(row=7, column=0, columnspan=2, pady=20)

noise = ttk.Button(text="noise-inconsistency",
                   style="my.TButton", command=noise_variance_inconsistency)
noise.grid(row=7, column=1, columnspan=2, pady=20)

copy_move = ttk.Button(text="Copy-Move", style="my.TButton", command=copy_move_forgery)
copy_move.grid(row=7, column=2, columnspan=1, pady=20)

image_stegnography = ttk.Button(text="Image-Extraction", style="my.TButton", command=image_decode)
image_stegnography.grid(row=8, column=2, pady=5)

String_analysis = ttk.Button(text="String Extraction", style="my.TButton", command=string_analysis)
String_analysis.grid(row=8, column=0, columnspan=1, pady=20)

style = ttk.Style()
style.configure('W.TButton', font = ('calibri', 10, 'bold'),foreground = 'red')

quitButton = ttk.Button(text="Exit program", style = 'W.TButton', command=root.quit)
quitButton.grid(row=7, column=1, pady=20)

root.geometry('')
root.mainloop()