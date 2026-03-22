from PIL import Image
from io import BytesIO
import pytesseract

def rm_transparent(img_bytes: bytes) -> bytes:
    image = Image.open(BytesIO(img_bytes))
    bg = Image.new("RGB", image.size, (255, 255, 255))
    img = Image.composite(image, bg, image)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def ocr_image(img_bytes):
    from PIL import Image
    from io import BytesIO
    import pytesseract

    image = Image.open(BytesIO(img_bytes))

    # 1️⃣ 灰度
    image = image.convert("L")

    # 2️⃣ 二值化（数字验证码推荐更强一点）
    image = image.point(lambda x: 0 if x < 150 else 255)

    # 3️⃣ OCR（限制只识别数字）
    text = pytesseract.image_to_string(
        image,
        config="--psm 6 -c tessedit_char_whitelist=0123456789"
    )

    # 4️⃣ 清洗结果（非常关键）
    text = "".join(filter(str.isdigit, text))

    return text