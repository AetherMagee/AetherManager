from PIL import Image, ImageDraw, ImageFont

def generate(text):
    image = Image.open("etc/gray_bg.jpg")
    editable = ImageDraw.Draw(image)
    font = ImageFont.truetype("etc/ShipporiAntique-Regular.ttf", 64)
    editable.text((70, 30), text=text, font=font)
    image.save(f"temp/code_{text}.jpg", optimize=True, quality=40)
