from flask import Flask, request, jsonify, send_from_directory
import json
import os
import requests
from Order import Order
from Fekra import Fekra
from whatsapp import send_whatsapp
from check_status import update_orders_status

app = Flask(__name__)

# Configuration
JSON_FILE = 'products.json'
STATIC_FOLDER = 'static'

# Ensure the JSON file exists
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'w') as f:
        json.dump([
            {
                "fekra_id": "aatr-sy-bashn-kod-63-dZEwji",
                "easy_order_id": "Tissot1853",
                "colors": [
                    {"fekra_id": "28-color-0", "easy_order_id": "اسود*اسود"}
                ],
                "price": 200,
                "commission": 20
            }
        ], f)

# Configuration
ORDERS_JSON_FILE = 'orders.json'

# Ensure the JSON file exists
if not os.path.exists(ORDERS_JSON_FILE):
    with open(ORDERS_JSON_FILE, 'w') as f:
        json.dump([
            {
                "easy_order_id": "saesfL3r324",
                "whatsapp_message_success": True,
                "reason_for_whatsapp_Failure": None,
                "customer_details": {
                    "name": "محمد محمود",
                    "phone": "01019689092",
                    "address": "شارع محمد محمود",
                    "state_value": 3,
                    "city_value": 150
                },
                "items": [
                    {
                        "id": "rolex-gold-kod6-ZBasJJ",
                        "color_id": "28-color-1",
                        "quantity": 1,
                        "price": 750,
                        "commission": 250,
                        "Sucesss": True,
                        "reasonForFailure": None
                    }
                ]
            }
        ], f)

# Add this near the top with other configuration
SETTINGS_JSON_FILE = 'settings.json'

# Ensure the settings.json file exists
if not os.path.exists(SETTINGS_JSON_FILE):
    with open(SETTINGS_JSON_FILE, 'w') as f:
        json.dump({
            "gemini_api_key": "",
            "fekra": {
                "email": "",
                "password": ""
            }
        }, f, indent=4)


# Helper functions
def read_products():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

def write_products(products):
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing to JSON file: {e}")
        return False

# Routes

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Get JSON payload
    print("Received webhook data:", data)

    with open('products.json', 'r', encoding='utf-8') as file:
        products = json.load(file)


    with open('settings.json', 'r') as f:
        settings = json.load(f)
        generative_api_key = settings.get("gemini_api_key")
        email = settings.get("fekra").get("email")
        password = settings.get("fekra").get("password")


    update_orders_status(email=email, password=password, api_key="66655b9c-e26a-4ad0-9d1c-b813a2d0e8b2", use_saved_cookies=True)
    # extract order details for fekra
    order = Order(easyOrder=data, generative_api_key=generative_api_key)
    customer_information, order_items, id = order.getFekraOrderDetails(products=products)

    print("customer_information", customer_information)
    print("order_items", order_items)

    error = None

    if customer_information["payment_method"] != "cod":
        order_details = {
            "id": id,
            "customer_details": customer_information,
            "items": order_items,
            "whatsapp_message_success": False,
            "reason_for_whatsapp_Failure": error,
            "Sucesss": False,
            "reasonForFailure": "دفع مقدم",
        }
        order.save_order(order=order_details)
        return {"status": "success"}, 200
    
    if customer_information["state_value"] is None:

        order_details = {
            "id": id,
            "customer_details": customer_information,
            "items": order_items,
            "whatsapp_message_success": False,
            "reason_for_whatsapp_Failure": error,
            "Sucesss": False,
            "reasonForFailure": "لم يتم التعرف علي المحافظة",
        }
        order.save_order(order=order_details)
        return {"status": "success"}, 200
    
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

    orders = fekra.make_order(customer_details=customer_information, orders=order_items)

    isAllOrderSucces = True

    for order_ in orders:
        if order_.get("Sucesss") == False:
            isAllOrderSucces = False
            break


    # send whatsapp message

    
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
        "Sucesss": isAllOrderSucces,
        "reasonForFailure": None,
    }
    order.save_order(order=order_details)
    

    return {"status": "success"}, 200

@app.route('/')
def home():
    return send_from_directory('.','products.html')

@app.route('/orders')
def orders():
    return send_from_directory('.','orders.html')


@app.route('/settings')
def settings():
    return send_from_directory('.','settings.html')

@app.route('/products.json')
def get_products_file():
    return send_from_directory('.', JSON_FILE)

@app.route('/api/products', methods=['GET'])
def get_products():
    products = read_products()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def create_product():
    products = read_products()
    new_product = request.json
    products.append(new_product)
    
    if write_products(products):
        return jsonify({"success": True, "message": "Product added successfully"}), 201
    return jsonify({"success": False, "message": "Failed to add product"}), 500

@app.route('/api/products/<int:index>', methods=['PUT'])
def update_product(index):
    products = read_products()
    
    if index < 0 or index >= len(products):
        return jsonify({"success": False, "message": "Product not found"}), 404
    
    products[index] = request.json
    
    if write_products(products):
        return jsonify({"success": True, "message": "Product updated successfully"})
    return jsonify({"success": False, "message": "Failed to update product"}), 500

@app.route('/api/products/<int:index>', methods=['DELETE'])
def delete_product(index):
    products = read_products()
    
    if index < 0 or index >= len(products):
        return jsonify({"success": False, "message": "Product not found"}), 404
    
    del products[index]
    
    if write_products(products):
        return jsonify({"success": True, "message": "Product deleted successfully"})
    return jsonify({"success": False, "message": "Failed to delete product"}), 500

@app.route('/api/save-products', methods=['POST'])
def save_all_products():
    new_products = request.json

    if write_products(new_products):
        return jsonify({"success": True, "message": "Products saved successfully"})
    return jsonify({"success": False, "message": "Failed to save products"}), 500


@app.route('/api/orders')
def get_orders():
    # Read orders from JSON file
    with open(ORDERS_JSON_FILE, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    return jsonify(orders)


# Helper functions for settings
def read_settings():
    try:
        with open(SETTINGS_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading settings file: {e}")
        return {
            "gemini_api_key": "",
            "fekra": {
                "email": "",
                "password": ""
            }
        }

def write_settings(settings):
    try:
        with open(SETTINGS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing to settings file: {e}")
        return False

# Add these routes for settings
@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = read_settings()
    return jsonify(settings)

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    new_settings = request.json
    if write_settings(new_settings):
        return jsonify({"success": True, "message": "Settings updated successfully"})
    return jsonify({"success": False, "message": "Failed to update settings"}), 500

@app.route('/api/settings/gemini', methods=['PUT'])
def update_gemini_key():
    settings = read_settings()
    data = request.json
    
    if 'api_key' in data:
        settings['gemini_api_key'] = data['api_key']
        
        if write_settings(settings):
            return jsonify({"success": True, "message": "Gemini API key updated successfully"})
    
    return jsonify({"success": False, "message": "Failed to update Gemini API key"}), 400

@app.route('/api/settings/fekra', methods=['PUT'])
def update_fekra_credentials():
    settings = read_settings()
    data = request.json
    
    if 'email' in data and 'password' in data:
        settings['fekra']['email'] = data['email']
        settings['fekra']['password'] = data['password']
        
        if write_settings(settings):
            return jsonify({"success": True, "message": "Fekra credentials updated successfully"})
    
    return jsonify({"success": False, "message": "Failed to update Fekra credentials"}), 400


# Add this route to proxy WhatsApp status requests
@app.route('/api/whatsapp-status', methods=['GET'])
def whatsapp_status():
    try:
        response = requests.get('http://45.61.129.15:3000/api/session/admin2/status', timeout=100)
        return response.json(), response.status_code
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
if __name__ == '__main__':
    app.run(debug=True)