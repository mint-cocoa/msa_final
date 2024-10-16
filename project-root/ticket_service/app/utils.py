import qrcode
import base64
from io import BytesIO

def generate_qr_code(ticket_data: dict) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket_data)        
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return img_str

def create_ticket(ticket_data: dict):
    ticket = models.Ticket(**ticket_data)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

