import requests
from bs4 import BeautifulSoup
import json
import concurrent.futures
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

def create_session():
    """Create a new requests session with appropriate headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    return session

def get_cookies_path(email):
    """Generate the path to the cookies file for a given email."""
    cookies_dir = "cookies"
    if not os.path.exists(cookies_dir):
        os.makedirs(cookies_dir)
    return os.path.join(cookies_dir, f"fekraa_{email.replace('@', '_at_')}.json")

def save_cookies(session, email):
    """Save session cookies to a file."""
    cookies_file = get_cookies_path(email)
    with open(cookies_file, 'w') as f:
        json.dump(session.cookies.get_dict(), f)
    print(f"Cookies saved to {cookies_file}")
    return True

def load_cookies(session, email):
    """Load cookies from a saved file into the session."""
    try:
        cookies_file = get_cookies_path(email)
        if not os.path.exists(cookies_file):
            print(f"Cookie file not found: {cookies_file}")
            return False
        
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        print(f"Cookies loaded successfully from {cookies_file}")
        return True
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

def login(session, base_url, email, password):
    """Log in to the Fekraa website and save cookies."""
    try:
        login_url = f"{base_url}/auth/login"
        response = session.get(login_url)
        
        # Extract CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        token_element = soup.select_one('input[name="_token"]')
        token = token_element['value'] if token_element else None
        
        # Prepare login data
        login_data = {
            "email": email,
            "password": password,
            "remember": "on"  # Check "Remember me" box
        }
        
        # Add CSRF token if found
        if token:
            login_data["_token"] = token
        
        # Submit the login form
        login_response = session.post(login_url, data=login_data, allow_redirects=True)
        
        # Save cookies
        save_cookies(session, email)
        
        print("Login successful!")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def initialize_session(email, password, base_url, use_saved_cookies=True):
    """Initialize a session, either with saved cookies or fresh login."""
    session = create_session()
    
    if use_saved_cookies and load_cookies(session, email):
        # Verify that we're actually logged in
        response = session.get(f"{base_url}")
        if "/auth/login" in response.url:
            print("Saved cookies expired, logging in...")
            login(session, base_url, email, password)
    else:
        # No saved cookies or loading failed, do a fresh login
        login(session, base_url, email, password)
    
    return session

def check_order_status(session, base_url, phone, timestamp=None):
    """Check the status of an order using the phone number."""
    try:
        # Build the URL with query parameters
        url = f"{base_url}/orders/list/all"
        params = {"search": phone}
        
        if timestamp:
            from_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            to_date = (datetime.fromtimestamp(timestamp) + timedelta(days=1)).strftime('%Y-%m-%d')
            params["from_date"] = from_date
            params["to_date"] = to_date
        
        # Make the HTTP request
        response = session.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return f"Error: HTTP status code {response.status_code}"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table
        table = soup.find('table', id='theTable')
        if not table:
            return "Error: Table not found on page"
        
        # Find order rows
        tbody = table.find('tbody')
        if not tbody:
            return "No orders found"
        
        order_rows = tbody.find_all('tr', class_=lambda c: c and 'status-' in c)
        if not order_rows:
            return "No orders found"
        
        # Get the first order row
        first_row = order_rows[0]
        
        # Try to get status from the status column (11th column)
        try:
            columns = first_row.find_all('td')
            if len(columns) > 10:
                status_column = columns[10]
                status_text = status_column.get_text(strip=True)
                if status_text:
                    return status_text
        except (IndexError, AttributeError):
            pass
        
        # If column extraction fails, extract status from the row class
        row_class = first_row.get('class', [])
        status_classes = [cls for cls in row_class if cls.startswith("status-")]
        if status_classes:
            status = status_classes[0].replace("status-", "")
            return status
        
        return "Status not found"
        
    except requests.Timeout:
        return "Request timeout"
    except requests.RequestException as e:
        return f"Error: Request failed: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def update_order_status(api_key, order_id, new_status):
    """
    Update the status of an order in the Easy Orders API.
    
    Args:
        api_key (str): The API key for authentication
        order_id (str): The order ID to update
        new_status (str): The new status to set
        
    Returns:
        dict: The JSON response from the API
    """
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

def map_fekra_status_to_easy_status(fekra_status):
    """
    Map Fekra status to Easy Orders status.
    
    Args:
        fekra_status (str): The status from Fekra
        
    Returns:
        str: The corresponding Easy Orders status
    """
    # This is a placeholder mapping - adjust based on actual Fekra statuses
    status_map = {
        "معلقة": "pending",
        "قيد الانتظار": "pending_payment",
        "شحنات مؤكدة": "paid",
        "تحت التحضير": "processing",
        "تم التحضير": "waiting_for_pickup",
        "في الشحن": "in_delivery",
        "تم التوصيل": "delivered",
        "ملغاه": "canceled",
        "مرفوضة": "returning_from_delivery"
    }

    
    return status_map.get(fekra_status, "pending")  # Default to pending if unknown

def process_order(order, session, base_url, api_key=None):
    """Process a single order to check its status and optionally update it in Easy Orders."""
    phone = order['customer_details']['phone']
    
    print("phone", phone)
    current_status = check_order_status(session, base_url, phone)
    
    print("current_state", current_status)
    final_status_list = ["ملغاه", "مرفوضة", "تم التوصيل"]
    
    if current_status in ["No orders found", "Request timeout", "Status not found"] or current_status.startswith("Error:"):
        return {
            'order': order,
            'status_changed': False,
            'remove': False,
            'update_result': None
        }
    
    update_result = None
    if order['order_status'] != current_status:
        # Status has changed
        if api_key and 'easy_order_id' in order:
            try:
                # Map Fekra status to Easy Orders status
                easy_status = map_fekra_status_to_easy_status(current_status)
                
                # Update status in Easy Orders
                update_result = update_order_status(api_key, order['easy_order_id'], easy_status)
                print(f"Updated order {order['easy_order_id']} in Easy Orders to {easy_status}")
            except Exception as e:
                print(f"Failed to update order {order['easy_order_id']} in Easy Orders: {e}")
                update_result = {"error": str(e)}
        
        result = {
            'order': order,
            'status_changed': True,
            'old_status': order['order_status'],
            'new_status': current_status,
            'remove': current_status in final_status_list,
            'update_result': update_result
        }
        order['order_status'] = current_status
        return result
    
    return {
        'order': order,
        'status_changed': False,
        'remove': False,
        'update_result': None
    }

def check_orders_status(session, base_url, api_key=None, orders_file='orders.json', max_workers=10):
    """
    Check the status of all orders in parallel and optionally update them in Easy Orders.
    
    Args:
        session: The requests session
        base_url: The base URL for Fekra
        api_key (str, optional): The API key for Easy Orders to update statuses
        orders_file (str): The path to the JSON file containing orders
        max_workers (int): The maximum number of concurrent workers
        
    Returns:
        list: The orders with changed statuses
    """
    with open(orders_file, 'r', encoding='utf-8') as file:
        orders = json.load(file)
    
    changed_orders = []
    
    # Process orders concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a partial function that includes session and base_url
        futures = [executor.submit(process_order, order, session, base_url, api_key) for order in orders]
        results = [future.result() for future in futures]
    
    # Handle results
    orders_to_keep = []
    for result in results:
        order = result['order']
        
        if result['status_changed']:
            changed_order = {
                'easy_order_id': order.get('easy_order_id', 'Unknown'),
                'old_status': result['old_status'],
                'new_status': result['new_status'],
                'customer_details': order['customer_details']
            }
            
            if result['update_result']:
                changed_order['update_result'] = result['update_result']
                
            changed_orders.append(changed_order)
        
        if not result['remove']:
            orders_to_keep.append(order)
    
    print("orders_to_keep", orders_to_keep)
    # Save only the orders to keep
    with open(orders_file, 'w', encoding='utf-8') as file:
        json.dump(orders_to_keep, file, ensure_ascii=False, indent=4)
    
    return changed_orders

def update_orders_status(email, password, api_key=None, base_url="https://fekraa1.com/affiliate", use_saved_cookies=True):
    """
    Main function to run the Fekra client and optionally update orders in Easy Orders.
    
    Args:
        email (str): Email for Fekra login
        password (str): Password for Fekra login
        api_key (str, optional): API key for Easy Orders to update statuses
        base_url (str): The base URL for Fekra
        use_saved_cookies (bool): Whether to use saved cookies
        
    Returns:
        list: The orders with changed statuses
    """
    session = initialize_session(email, password, base_url, use_saved_cookies)
    changed_orders = check_orders_status(session, base_url, api_key)
    return changed_orders

# if __name__ == "__main__":
#     # Example API key - replace with your actual key
#     api_key = "66655b9c-e26a-4ad0-9d1c-b813a2d0e8b2"
    
#     changed_orders = update_orders_status(
#         email="mosahsa040@gmail.com",
#         password="XeCZpnS98pWNdpM",
#         api_key=api_key,
#         use_saved_cookies=True
#     )
#     print(changed_orders)