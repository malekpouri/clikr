import qrcode
import base64
from io import BytesIO


def generate_qr_code(url: str) -> str:
    """تولید کد QR برای یک URL و برگرداندن آن به صورت base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # تبدیل تصویر به base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def generate_qr_code_file(url: str) -> BytesIO:
    """تولید کد QR برای یک URL و برگرداندن آن به صورت فایل"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # ذخیره تصویر در حافظه
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)

    return buffered