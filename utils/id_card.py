import os
import qrcode

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def create_student_card(
    name,
    student_number,
    photo_path,
    logo_path
):

    os.makedirs("cards", exist_ok=True)
    os.makedirs("qr", exist_ok=True)

    qr_path = f"qr/{student_number}.png"

    qr = qrcode.make(student_number)
    qr.save(qr_path)

    card = Image.new(
        "RGB",
        (900, 550),
        "white"
    )

    draw = ImageDraw.Draw(card)

    try:
        font_big = ImageFont.truetype(
            "arial.ttf",
            36
        )

        font_small = ImageFont.truetype(
            "arial.ttf",
            24
        )

    except:

        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    if os.path.exists(logo_path):

        logo = Image.open(logo_path)

        logo.thumbnail((180, 180))

        card.paste(
            logo,
            (30, 30)
        )

    student = Image.open(photo_path)

    student = student.resize(
        (220, 260)
    )

    card.paste(
        student,
        (40, 220)
    )

    qr = Image.open(qr_path)

    qr = qr.resize(
        (180, 180)
    )

    card.paste(
        qr,
        (680, 330)
    )

    draw.text(
        (300, 80),
        "ALBARMAWI PRIVATE SCHOOL",
        fill="black",
        font=font_big
    )

    draw.text(
        (300, 180),
        f"Name : {name}",
        fill="black",
        font=font_small
    )

    draw.text(
        (300, 240),
        f"ID : {student_number}",
        fill="black",
        font=font_small
    )

    output = f"cards/{student_number}.png"

    card.save(output)

    return output
