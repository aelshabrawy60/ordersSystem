import requests
import base64
import time
from PIL import Image
import io
import copy
import textwrap


# API base URL - change to your server address
API_URL = "http://45.61.129.15:3000"

def check_status():
    """Check the status of the WhatsApp client"""
    response = requests.get(f"{API_URL}/status")
    return response.json()

def display_qr_code(qr_data_url):
    """Display QR code from data URL"""
    # Extract base64 data from data URL
    base64_data = qr_data_url.split(',')[1]
    qr_image_data = base64.b64decode(base64_data)
    
    # Open and display the image
    img = Image.open(io.BytesIO(qr_image_data))
    img.show()
    print("Scan the QR code with your WhatsApp to authenticate")

def send_whatsapp_message(phone_number, message_text):
    """Send a WhatsApp message"""
    payload = {
        "number": phone_number,  
        "message": message_text
    }
    
    response = requests.post(f"{API_URL}/send-message", json=payload)
    return response.json()

def send_whatsapp(customer_information, order_details, products):
    phone_number = "2" + customer_information["phone"]
    # First check the status
    status = check_status()
    
    # If authentication is needed, display QR code
    if status.get('status') == 'need_auth':
        display_qr_code(status['qrCode'])
        
        return False, None, status['qrCode']
    
    # Now send a message
    message = create_order_message(name=customer_information["name"], order_items=order_details, products=products, total_price=customer_information["total_cost"])
    
    result = send_whatsapp_message(phone_number, message)
    print(f"Message send result: {result}")

    if result.get('status') == 'success':
        return True, None, None
    else:
        return False, result.get('message'), None

if __name__ == "__main__":
    send_whatsapp_message(phone_number="+201147009632", message_text=".")


def create_order_message(name, order_items, products, total_price):

    order_items_copy = copy.deepcopy(order_items)

    for item in order_items_copy:
        product = next((item_ for item_ in products if item_["fekra_id"] == item.get("id")), None)

        print(product)
        print(item)
        if not product:
            item["Sucesss"] = False
            item["reasonForFailure"] = "لم يتم التعرف علي المنتج"
            continue

        fekra_color = None

        if not len(product.get("colors")) == 0:
            color = next((color for color in product.get("colors") if color.get("fekra_id") == item.get("color_id")), None)

            if not color:
                item["Sucesss"] = False
                item["reasonForFailure"] = "لم يتم التعرف علي اللون"
                continue

            color = color.get("easy_order_id")

        item.update(
            {
                "id": product.get("easy_order_id"),
                "color_id": color,
            }
        )


    

    """Create a message for the order"""
    message = f"""‏السيد/ة \n{name} \n\n """
    message += textwrap.dedent("""
        شكرًا لثقتك بمنتجات Pretful!
        لقد استلمنا طلبك بكل سعادة، ونسعى لتقديم تجربة استثنائية تعكس الفخامة والأناقة التي تستحقها.
        إذا كان لديك أي استفسار أو طلب إضافي، لا تتردد في التواصل معنا.
        نقدّر اختيارك ونأمل أن تنال ساعتك إعجابك.
        طلبك هو :\n
        """)

    for item in order_items_copy:
        # Don't show quantity when it's 0
        if item['quantity'] <= 1:
            message += f"\u200F• {item['id']} \u200F(اللون: {item['color_id']})\n"
        else:
            message += f"\u200F• {item['id']} \u200F(اللون: {item['color_id']}، الكمية: {item['quantity']})\n"

    message += f"\u200F الاجمالي {total_price}\n"
    message += textwrap.dedent("""
        ، وسيتم التواصل معك هاتفيا او عبر الواتس للتأكيد من قبل فريق العمل.
        (🛑ملحوظة الرقم الي هيتصل بحضرتك ده للتأكيد الطلب فقط مره واحدة فقط التواصل بيكون علي ارقمنا الوحيدة المذكورة علي الموقع علي الواتس فقط)
        شكرا لختيارك Pretful😍
        نتمني لك يوم سعيد
        مع اطيب التحيات،
        فريق pretful.
        """)
    
    return message
