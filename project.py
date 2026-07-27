import qrcode

# QR kodga kiritiladigan hash matni
hash_text = "ba37c3651ed4467a93d0cd502bcb28b"

# QR kod obyektini yaratish
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4,
)
qr.add_data(hash_text)
qr.make(fit=True)

# Rasmni saqlash
img = qr.make_image(fill_color="black", back_color="white")
img.save("qrcode.png")

print("QR kod muvaffaqiyatli yaratildi va qrcode.png sifatida saqlandi!")