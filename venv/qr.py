import qrcode

# URL to encode
url = "https://www.kaspersky.com/resource-center/threats/what-is-cybercrime"

# Create QR code instance
qr = qrcode.QRCode(
    version=1,  # 1 is smallest, up to 40 (more data = larger version)
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # high error correction
    box_size=10,  # size of each box in pixels
    border=4,  # border thickness (default is 4)
)

# Add the URL
qr.add_data(url)
qr.make(fit=True)

# Generate the image
img = qr.make_image(fill_color="black", back_color="white")

# Save the image to a file
img.save("cybercrime_qr.png")

print("QR code generated and saved as 'cybercrime_qr.png'")
