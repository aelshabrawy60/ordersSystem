from flask import Flask, request
from Order import Order
from Fekra import Fekra
from whatsapp import send_whatsapp
import json



def testSystem():
    with open('testOrder.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    print("Received webhook data:", data)

    with open('products.json', 'r', encoding='utf-8') as file:
        products = json.load(file)


    with open('settings.json', 'r') as f:
        settings = json.load(f)
        generative_api_key = settings.get("gemini_api_key")
        email = settings.get("fekra").get("email")
        password = settings.get("fekra").get("password")


    # extract order details for fekra
    order = Order(easyOrder=data, generative_api_key=generative_api_key)
    customer_information, order_items, id = order.getFekraOrderDetails(products=products)

    print("customer_information", customer_information)
    print("order_items", order_items)

    error = None

    if customer_information["city_value"] is None:

        order_details = {
            "id": id,
            "customer_details": customer_information,
            "items": order_items,
            "whatsapp_message_success": False,
            "reason_for_whatsapp_Failure": error,
            "Sucesss": False,
            "reasonForFailure": "لم يتم التعرف علي المدينة",
        }
        order.save_order(order=order_details)
        return {"status": "success"}, 200
    
    if customer_information["note"] == True:
        order_details = {
            "id": id,
            "customer_details": customer_information,
            "items": order_items,
            "whatsapp_message_success": False,
            "reason_for_whatsapp_Failure": error,
            "Sucesss": False,
            "reasonForFailure": "يحتوي علي ملاحظة",
        }
        order.save_order(order=order_details)
        return {"status": "success"}, 200

    
    fekra = Fekra(
        email=email,
        password=password,
        use_saved_cookies=False
    )

    fekra.make_order(customer_details=customer_information, orders=order_items)

    #send whatsapp message

    
    try:
        status, error, qrCode = send_whatsapp(
            customer_information=customer_information,
            order_details=order_items,
            products=products,
        )
    except Exception as e:
        status = False
        error = str(e)

    if not status and not error:
        error = "يتطلب تسجيل الدخول"
    
    order_details = {
        "id": id,
        "customer_details": customer_information,
        "items": order_items,
        "whatsapp_message_success": True if status else False,
        "reason_for_whatsapp_Failure": error,
        "Sucesss": True if status else False,
        "reasonForFailure": None,
    }
    order.save_order(order=order_details)
    

    return {"status": "success"}, 200


testSystem()


# fekra emails
# mosahsa040@gmail.com
# XeCZpnS98pWNdpM