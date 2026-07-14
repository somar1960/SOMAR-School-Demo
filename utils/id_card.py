import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def create_student_card(name, student_number, photo_bytes, logo_bytes=None, school_name="SOMAR School"):
    """
    Create a student ID card and return as BytesIO object (PNG).
    All inputs are BytesIO streams (photo, logo).
    """
    card = Image.new("RGB", (900, 550), "white")
    draw = ImageDraw.Draw(card)

    # Load fonts (try to use a nicer font if available, else default)
    try:
        font_big = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Logo (top left)
    if logo_bytes:
        logo = Image.open(logo_bytes)
        logo.thumbnail((180, 180))
        card.paste(logo, (30, 30))

    # Student photo
    student_img = Image.open(photo_bytes)
    student_img = student_img.resize((220, 260))
    card.paste(student_img, (40, 220))

    # QR code
    qr = qrcode.make(student_number)
    qr_bytes = BytesIO()
    qr.save(qr_bytes, format="PNG")
    qr_bytes.seek(0)
    qr_img = Image.open(qr_bytes)
    qr_img = qr_img.resize((180, 180))
    card.paste(qr_img, (680, 330))

    # Draw school name
    draw.text((300, 80), school_name, fill="black", font=font_big)
    draw.text((300, 180), f"Name: {name}", fill="black", font=font_small)
    draw.text((300, 240), f"ID: {student_number}", fill="black", font=font_small)

    # Save card to BytesIO
    output = BytesIO()
    card.save(output, format="PNG")
    output.seek(0)
    return output
