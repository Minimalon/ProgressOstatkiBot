import os, re
import smtplib
from email.mime.text import MIMEText
import mimetypes
from email import encoders
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import math
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

import config, cashInfo


# def get_last_file(cash):
#     cash = 'cash-' + cash
#     cash_info = [line.split() for line in open(linuxcasneserveserveinfo.txt', 'r') if re.search(cash, line)]
#     path = linuxcasneserveserveostatk' + cash_info[0][1] + ' + cash_info[0][2] + xls'
#     files = os.listdir(path)
#     files = [os.path.join(path, file) for file in files]
#     files = [file for file in files if os.path.isfile(file)]
#     return max(files, key=os.path.getctime)
#
# def get_last_files(cash, amount):
#     cash = 'cash-' + cash
#     cash_info = [line.split() for line in open(linuxcasneserveserveinfo.txt', 'r') if re.search(cash, line)]
#     cash_path = linuxcasneserveserveostatk' + cash_info[0][1] + ' + cash_info[0][2] + xls'
#     files = os.listdir(cash_path)
#     files = [os.path.join(cash_path, file) for file in files]
#     files = [file for file in files if os.path.isfile(file)]
#     files = sorted(files, key=os.path.getctime)
#     files.reverse()
#     return [ files[el] for el in range(amount) ]

def get_last_file(cash):
    cash = 'cash-' + cash
    cash_info = [line.split() for line in open(f'{config.server_path}info.txt', 'r')
                 if re.search(cash, line)]
    path = f'{config.server_path}ostatki/' + cash_info[0][1] + '/' + cash_info[0][2] + '/xls'
    files = os.listdir(path)
    files = [os.path.join(path, file) for file in files]
    files = [file for file in files if os.path.isfile(file)]
    return max(files, key=os.path.getctime)


def get_last_files(cash, amount):
    cash = 'cash-' + cash
    cash_info = [line.split() for line in open(f'{config.server_path}info.txt', 'r') if
                 re.search(cash, line)]
    cash_path = f'{config.server_path}ostatki/' + cash_info[0][1] + "/" + cash_info[0][2] + '/xls'
    files = os.listdir(cash_path)
    files = [os.path.join(cash_path, file) for file in files]
    files = [file for file in files if os.path.isfile(file)]
    files = sorted(files, key=os.path.getctime)
    files.reverse()
    return [files[el] for el in range(amount)]


def send_email(email, path):
    sender = config.email_login
    password = config.email_password

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    try:
        server.login(sender, password)
        msg = MIMEMultipart()
        msg["Subject"] = "OSTATKI"
        msg["From"] = sender
        msg["To"] = email
        msg['Date'] = formatdate(localtime=True)
        ftype, encoding = mimetypes.guess_type(path)
        file_type, subtype = ftype.split('/')
        if file_type == 'image':
            msg["Subject"] = "Barcode"
            with open(path, 'rb') as f:
                file = MIMEImage(f.read(), subtype)
        else:
            msg["Subject"] = "OSTATKI"
            file = MIMEBase('application', "octet-stream")
            file.set_payload(open(path, "rb").read())
            encoders.encode_base64(file)
        file.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(path))
        msg.attach(file)

        server.sendmail(sender, email, msg.as_string())

        # server.sendmail(sender, sender, f"Subject: CLICK ME PLEASE!\n{message}")
    except Exception as _ex:
        print(_ex)
        pass


def get_valid_barcode(pcNumber):
    barcode = pcNumber.split('-')[0]
    pcNumber = pcNumber.split('-')[0]
    if len(pcNumber) == 1:
        barcode += "000000"
    if len(pcNumber) == 2:
        barcode += "00000"
    if len(pcNumber) == 3:
        barcode += "0000"
    if len(pcNumber) == 4:
        barcode += "000"
    count_busy_barcode = [barcode for line in open(config.dir_path + 'logs/busy_barcode.txt', 'r') if re.search(barcode, line)]
    with open(config.dir_path + 'logs/busy_barcode.txt', 'a') as file:
        barcode = barcode + str(len(count_busy_barcode))
        file.write(str(barcode) + '\n')
    return str(barcode)


def generate_barcode(barcode_number):
    my_code = Code128(barcode_number, writer=ImageWriter())
    my_code.save(config.dir_path + "logs/barcode", options={"write_text": False})


def resize_canvas(old_image_path, msg):
    print(old_image_path)
    im = Image.open(old_image_path)
    old_width, old_height = im.size

    if 15 < len(msg) <= 25:
        canvas_width = old_width + 50
    elif len(msg) > 25:
        canvas_width = old_width + 130
    elif len(msg) < 15:
        canvas_width = old_width
    else:
        canvas_width = old_width + 50

    canvas_height = old_height + 50

    x1 = int(math.floor((canvas_width - old_width) / 2))
    y1 = int(math.floor((canvas_height - old_height) / 2))

    mode = im.mode
    if len(mode) == 1:  # L, 1
        new_background = (255)
    if len(mode) == 3:  # RGB
        new_background = (255, 255, 255)
    if len(mode) == 4:  # RGBA, CMYK
        new_background = (255, 255, 255, 255)

    newImage = Image.new(mode, (canvas_width, canvas_height), new_background)
    newImage.paste(im, (x1, y1, x1 + old_width, y1 + old_height))
    draw = ImageDraw.Draw(newImage)

    font = ImageFont.truetype(config.dir_path + "Ermilov-bold.otf", 18)

    width_text, height_text = font.getsize(msg)

    w, h = draw.textsize(msg, font=font)
    xy = (((canvas_width - w) / 2), 5)

    draw.text(xy, msg, font=font, fill="black")
    newImage.save(old_image_path)
