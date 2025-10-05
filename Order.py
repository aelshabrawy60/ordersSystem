from City import City
import json
from datetime import datetime
import requests
import math

def ceil_to_highest_5(number: int) -> int:
    return math.ceil(number / 5) * 5

class Order:
    def __init__(self, easyOrder, generative_api_key):
        self.easyOrder = easyOrder
        with open('governments.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        self.government = next(
            (item for item in data if item.get("name", "").strip() == self.easyOrder.get("government", "").strip()), 
            None
        )

        self.city_code = None

        if self.government:
            self.City = City(cities=self.government["cities"], city=self.easyOrder.get("country"), address=self.easyOrder.get("address"), generative_api_key=generative_api_key)
            self.city_code = self.City.get_city_code()

            if self.city_code == False:
                # try to extract the government code in case user has enterd wrong government
                self.extracted_government_code = self.City.extract_government_code()

                if self.extracted_government_code != False:

                    user_enterd_government_code = self.government["value"] if self.government else None
                    if user_enterd_government_code != self.extracted_government_code :
                        # try to extract city again with the new extracted government code
                        print("correcting government needed")
                        self.government = next(
                            (item for item in data if item.get("value") == self.extracted_government_code), 
                            None
                        )
                        self.newCity = City(cities=self.government["cities"], city=self.easyOrder.get("country"), address=self.easyOrder.get("address"), generative_api_key=generative_api_key)
                        self.city_code = self.newCity.get_city_code()

                        if self.city_code == False:
                            # complex solution
                            print("complex solution needed")
                            pass
                    else :
                        # complex solution
                        print("complex solution needed")
                        pass



        hasNote = self.easyOrder.get("note") is not None and len(self.easyOrder.get("note")) > 0
        self.customer_information = {
            "name": self.easyOrder.get("full_name"),
            "phone": self.easyOrder.get("phone"),
            "address": self.easyOrder.get("address"),
            "state_value": self.government["value"] if self.government else None,
            "city_value": self.city_code if self.city_code else None,
            "note": hasNote,
            "total_cost": ceil_to_highest_5(self.easyOrder.get("total_cost")),
            "payment_method": self.easyOrder.get("payment_method"),
        }
        pass

    


    def get_state_value(self):
        return
    def extract_city_value(self):
        return
    def getFekraOrderDetails(self, products):
        id = self.easyOrder.get("id")

        order_items = []
        for item in self.easyOrder.get("cart_items"):
            product = next((item_ for item_ in products if item_["easy_order_id"] == item.get("product").get("name")), None)

            if not product:
                order_items.append(
                    {
                        "Sucesss": False,
                        "reasonForFailure": "لم يتم التعرف علي المنتج",
                    }
                )
                print("product not found on fekra")
                continue

            fekra_color = None

            if not len(product.get("colors")) == 0:
                easy_order_color = item.get("variant").get("variation_props")[0].get("variation_prop")
                color = next(
                    (color for color in product.get("colors", []) 
                    if str(color.get("easy_order_id", "")).strip() == str(easy_order_color).strip()), 
                    None
                )


                if not color:
                    order_items.append(
                        {
                            "Sucesss": False,
                            "reasonForFailure": "لم يتم التعرف علي اللون",
                        }
                    )
                    print("color not found on fekra")
                    continue

                fekra_color = color.get("fekra_id")

            order_items.append(
                {
                    "Sucesss": True,
                    "reasonForFailure": None,
                    "id": product.get("fekra_id"),
                    "color_id": fekra_color,
                    "quantity": item.get("quantity"),
                    "price": product.get("price"),
                    "commission": product.get("commission"),
                }
            )

        return self.customer_information, order_items, id
    
    def save_order(self, order):
        new_order = {
            "easy_order_id": order.get("id"),
            "whatsapp_message_success": order.get("whatsapp_message_success"),
            "reason_for_whatsapp_Failure": order.get("reason_for_whatsapp_Failure"),
            "order_status": "معلقة",
            "date": datetime.now().timestamp(),
            "customer_details": order.get("customer_details"),
            "items": order.get("items"),
            "Sucesss": order.get("Sucesss"),
            "reasonForFailure": order.get("reasonForFailure"),
        }

        try:
            with open('orders.json', "r", encoding='utf-8') as file:
                data = json.load(file)  # Load existing JSON data
        except (FileNotFoundError, json.JSONDecodeError):
                data = []  # Initialize as empty list if file doesn't exist or is empty

        data.append(new_order)

        # Write back to the file
        with open('orders.json', "w", encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def update_order_status(self,api_key, order_id, new_status):
        # Valid statuses
        valid_statuses = [
            "pending", "confirmed", "pending_payment", "paid", "paid_failed",
            "processing", "waiting_for_pickup", "in_delivery", "delivered",
            "canceled", "returning_from_delivery", "request_refund",
            "refund_in_progress", "refunded"
        ]
        
        # Validate status
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # API endpoint
        url = f"https://api.easy-orders.net/api/v1/external-apps/orders/{order_id}/status"
        
        # Headers and payload
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "status": new_status
        }
        
        # Make the request
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()


if __name__ == "__main__":

    with open('settings.json', 'r') as f:
        settings = json.load(f)
        generative_api_key = settings.get("gemini_api_key")
        email = settings.get("fekra").get("email")
        password = settings.get("fekra").get("password")

    with open("testOrder.json", "r", encoding="utf-8") as file:
            data = json.load(file)

    order = Order(easyOrder=data, generative_api_key=generative_api_key)
    print(order.customer_information)