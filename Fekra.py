from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import concurrent.futures


class Fekra:
    def __init__(self, email, password, use_saved_cookies=True):
         # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize Chrome with headless options
        self.driver = webdriver.Chrome(options=chrome_options)


        self.email = email
        self.password = password
        # Try to load cookies if requested
        if use_saved_cookies and self.load_cookies():
            # Verify that we're actually logged in
            #self.driver.get("https://fekraa1.com/affiliate")
            # Check if we're redirected to login page
            if "/auth/login" in self.driver.current_url:
                print("Saved cookies expired, logging in...")
                self.login()
        else:
            # No saved cookies or loading failed, do a fresh login
            self.login()        
        


    

    def select_color(self, color_id):
        """
        Select a color from the color options with improved interaction handling.
        
        Args:
            color_id: The ID of the color element to select
        """
        try:
            # Wait for the element to be present
            wait = WebDriverWait(self.driver, 2)
            radio_element = wait.until(EC.presence_of_element_located((By.ID, color_id)))
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", radio_element)
            time.sleep(0.5)  # Brief pause after scrolling
            
            # Try regular click first
            try:
                wait.until(EC.element_to_be_clickable((By.ID, color_id)))
                radio_element.click()
            except:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", radio_element)
            
            print(f"Color {color_id} selected successfully!")
        except Exception as e:
            print(f"Error selecting color: {e}")

    def fill_customer_information(self, full_name, phone_number, address ,whatsapp_number=None, state_value=None, city_value=None):
        """
        Fill the customer information form using Selenium WebDriver
        
        Parameters:
        - driver: Selenium WebDriver instance
        - full_name: Customer's full name
        - phone_number: Customer's phone number (must be 11 digits)
        - whatsapp_number: Optional WhatsApp number
        - state_value: Value of the state to select (numeric ID)
        - city_value: Value of the city to select (numeric ID)
        """
        try:
            
            # Fill the full name field
            name_field = self.driver.find_element(By.ID, "receiver_name")
            name_field.clear()
            name_field.send_keys(full_name)
            
            # Fill the phone number field
            phone_field = self.driver.find_element(By.ID, "receiver_phone")
            phone_field.clear()
            phone_field.send_keys(phone_number)
            
            # Fill the WhatsApp number if provided
            if whatsapp_number:
                whatsapp_field = self.driver.find_element(By.ID, "receiver_mobile")
                whatsapp_field.clear()
                whatsapp_field.send_keys(whatsapp_number)

            # Fill address
            if address:
                address_field = self.driver.find_element(By.ID, "receiver_address")
                address_field.clear()
                address_field.send_keys("".join(address.splitlines()))

            
            # Select state if provided
            if state_value:
                # Find and click on the state dropdown
                state_select = Select(self.driver.find_element(By.ID, "state_id"))
                state_select.select_by_value(str(state_value))
                
                # Wait for the city dropdown to be populated
                time.sleep(1)  # Allow some time for the AJAX request to complete
                
                # Select city if provided
                if city_value:
                    # Wait for city dropdown to be populated
                    wait = WebDriverWait(self.driver, 10)
                    city_select_element = wait.until(
                        EC.presence_of_element_located((By.ID, "city-select"))
                    )
                    city_select = Select(city_select_element)
                    city_select.select_by_value(str(city_value))
            
            time.sleep(3)
            print("Form filled successfully!")
            return True
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return False
        
    def update_cart_items(self, cart_items):
        """
        Updates quantities, prices, and commission values in the cart table
        
        Parameters:
        - driver: Selenium WebDriver instance
        - cart_items: List of dictionaries containing:
            - index: Index of the product in the cart (starting from 0)
            - quantity: Quantity to set
            - price: Price to set
            - commission: Commission/profit to set
        
        Returns:
        - True if successful, False otherwise
        """
        try:
            for item in cart_items:
                index = item['index']
                quantity = item['quantity']
                price = item['price']
                commission = item['commission']
                
                # Update quantity
                quantity_field = self.driver.find_element(By.ID, f"cartQuantity{index}")
                quantity_field.clear()
                quantity_field.send_keys(str(quantity))
                quantity_field.send_keys(Keys.TAB)
                time.sleep(0.3)  # Small delay to allow for any JS updates
                
                # Update price
                price_field = self.driver.find_element(By.ID, f"cartPrice{index}")
                price_field.clear()
                price_field.send_keys(str(price))
                price_field.send_keys(Keys.TAB)
                time.sleep(0.3)  # Small delay to allow for any JS updates
                
                # Update commission (note: may need to make editable first if readonly)
                #commission_field = self.driver.find_element(By.ID, f"cartCommission{index}")
                
                # Remove readonly attribute using JavaScript if needed
                # self.driver.execute_script("arguments[0].removeAttribute('readonly')", commission_field)
                
                # commission_field.clear()
                # commission_field.send_keys(str(commission))
                # commission_field.send_keys(Keys.TAB)
                
                # Make sure the product checkbox is checked
                product_checkbox = self.driver.find_element(By.ID, f"product_{index}")
                if not product_checkbox.is_selected():
                    product_checkbox.click()
                    
                # Verify values were set correctly
                print(f"Updated Product {index}:")
                print(f"  - Quantity: {quantity_field.get_attribute('value')}")
                print(f"  - Price: {price_field.get_attribute('value')}")
                #print(f"  - Commission: {commission_field.get_attribute('value')}")
                
            time.sleep(5)
            print("Cart items updated successfully!")
            return True
            
        except Exception as e:
            print(f"An error occurred while updating cart: {str(e)}")
            return False
        
    def submit_order(self, wait_time=10):
        """
        Finds and clicks the submit order button
        
        Parameters:
        - driver: Selenium WebDriver instance
        - wait_time: Maximum time to wait for button to be clickable (in seconds)
        
        Returns:
        - True if button was successfully clicked, False otherwise
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
        
        try:
            print("Attempting to find and click the submit order button...")
            
            # Wait for the button to be clickable
            wait = WebDriverWait(self.driver, wait_time)
            
            # Try multiple strategies to find the button
            locators = [
                # Strategy 1: By button text content
                (By.XPATH, "//button[contains(text(), 'تنفيذ الطلب')]"),
                
                # Strategy 2: By button classes and type
                (By.CSS_SELECTOR, "button.btn.btn-primary.pull-left[type='submit']"),
                
                # Strategy 3: More specific XPath with partial text and style
                (By.XPATH, "//button[@type='submit' and contains(@style, 'background-color: #000000') and contains(text(), 'تنفيذ الطلب')]")
            ]
            
            # Try each locator strategy
            for locator_type, locator_value in locators:
                try:
                    button = wait.until(EC.element_to_be_clickable((locator_type, locator_value)))
                    
                    # Scroll to the button to make sure it's in view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    
                    # Wait a moment after scrolling
                    import time
                    time.sleep(0.5)
                    
                    # Click the button
                    button.click()
                    
                    print("Submit order button clicked successfully!")
                    return True
                except (TimeoutException, ElementClickInterceptedException) as e:
                    # Continue to the next strategy if this one fails
                    continue
            
            # If we reach here, all strategies failed
            print("Could not find or click the submit order button using any strategy.")
            return False
            
        except Exception as e:
            print(f"Error clicking submit button: {str(e)}")
            return False

    def get_fekra_shipping_cost(self):
        shipping_element = self.driver.find_element(By.ID, "shipping_value")
        data_value = shipping_element.get_attribute("data-value")
        shipping_cost = int(float(data_value))
        return shipping_cost

    def setOrdersPrice(self, orders, total_cost, shipping_cost):
        orders_count = len(orders)
        
        if orders_count == 0:
            return orders  # Return an empty list if no orders exist
        
        order_price = (total_cost - shipping_cost) / orders_count

        for order in orders:
            order["price"] = order_price  # Assuming each order is a dictionary
        
        return orders

    def make_order(self, customer_details = None, orders= None):
        sucess_orders = 0
        for order in orders:
            if order.get("Sucesss"):
                self.add_product_to_cart(id=order["id"], color=order["color_id"])
                sucess_orders += 1
                time.sleep(1)

        if sucess_orders == 0:
            return orders
        
        
        self.driver.get("https://fekraa1.com/affiliate/shop-cart")

        time.sleep(2)
        # Fill customer information
        self.fill_customer_information(
            full_name=customer_details["name"] + "*",
            phone_number=customer_details["phone"],
            state_value=customer_details["state_value"],
            city_value=customer_details["city_value"],
            address=customer_details["address"],
        )

        shipping_cost = self.get_fekra_shipping_cost()
        total_cost = customer_details["total_cost"]

        orders = self.setOrdersPrice(shipping_cost=shipping_cost, total_cost=total_cost, orders=orders)

        #  Update cart items
        for index, order in enumerate(orders):
            self.update_cart_items(
                cart_items=[
                    {
                        "index": index,
                        "quantity": order["quantity"],
                        "price": order["price"],
                        "commission": order["commission"]
                    }
                ]
            )

        #place an order
        self.submit_order()
        time.sleep(5)
        
        # Check if redirect indicates successful order
        current_url = self.driver.current_url
        if current_url == "https://fekraa1.com/affiliate":
            # Orders added successfully
            pass
        else:
            # Orders not added successfully, set all to False
            for order in orders:
                order["Sucesss"] = False
                order["reasonForFailure"] = "Fekra failuer"
        
        self.driver.quit()  # Close the browser
        return orders
    
    def click_add_to_cart_button(self):
        """
        Click the "Buy Now" button on the page.
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            # Try multiple selectors in case one doesn't work
            selectors = [
                # Try by CSS class and Arabic text
                "//button[contains(@class, 'add-to-cart-btn')]",
                # Try by onclick attribute
                "//button[@onclick='addToCart()']",
                # Try by CSS class
                ".add-to-cart-btn",
            ]
            
            # Try each selector until one works
            for selector in selectors:
                try:
                    # Wait for the element to be clickable
                    if selector.startswith("//"):
                        # XPath selector
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS selector
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Click the button
                    element.click()
                    print("Buy Now button clicked successfully!")
                    return True
                except:
                    continue
                    
            raise Exception("Could not find Buy Now button using any selector")
            
        except Exception as e:
            print(f"Error clicking Buy Now button: {e}")
            return False
    
    def add_product_to_cart(self, id, color = None):
        self.driver.get(f"https://fekraa1.com/affiliate/product/{id}")
        if color:
            print("selcting color")
            self.select_color(color_id=color)
        time.sleep(1)
        self.click_add_to_cart_button()

    def login(self):
        """
        Log in to the Fekraa website using the provided email and password and save cookies
        """
        try:
            # Navigate to the login page
            self.driver.get("https://fekraa1.com/affiliate/auth/login")
            
            # Wait for the login form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "si-email"))
            )
            
            # Fill in email
            email_field = self.driver.find_element(By.ID, "si-email")
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Fill in password
            password_field = self.driver.find_element(By.ID, "si-password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Optional: Check "Remember me" box
            remember_me = self.driver.find_element(By.ID, "remember")
            if not remember_me.is_selected():
                remember_me.click()
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Wait for login to complete (wait for some element that appears after successful login)
            WebDriverWait(self.driver, 10).until(
                EC.url_changes("https://fekraa1.com/affiliate/auth/login")
            )
            
            # Get cookies after successful login
            cookies = self.driver.get_cookies()
            
            # Save cookies to a file
            import json
            import os
            
            cookies_dir = "cookies"
            if not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir)
                
            cookies_file = os.path.join(cookies_dir, f"fekraa_{self.email.replace('@', '_at_')}.json")
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f)
            
            print(f"Login successful! Cookies saved to {cookies_file}")
            return cookies
            
        except Exception as e:
            print(f"Login failed: {e}")
            return None
        
    def load_cookies(self, email=None):
        """
        Load cookies from a saved file and add them to the driver
        
        Args:
            email: Optional email to load specific cookies file.
                If None, uses the instance email
        
        Returns:
            bool: True if cookies were loaded successfully, False otherwise
        """
        try:
            import json
            import os
            
            # Use the provided email or fall back to the instance email
            email_to_use = email if email else self.email
            
            # Create the filename based on the email
            cookies_file = os.path.join("cookies", f"fekraa_{email_to_use.replace('@', '_at_')}.json")
            
            # Check if the file exists
            if not os.path.exists(cookies_file):
                print(f"Cookie file not found: {cookies_file}")
                return False
            
            # Load cookies from file
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Navigate to the domain first (required for setting cookies)
            self.driver.get("https://fekraa1.com")
            
            # Add each cookie to the browser
            for cookie in cookies:
                # Some drivers have issues with certain cookie attributes
                # Remove problematic attributes if they exist
                if 'expiry' in cookie:
                    del cookie['expiry']
                
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Warning: Couldn't add cookie {cookie.get('name')}: {e}")
            
            # Refresh the page to apply cookies
            self.driver.refresh()
            
            print(f"Cookies loaded successfully from {cookies_file}")
            return True
            
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
    


customer_details= {
    "name": "محمد محمود",
    "phone": "01019689092",
    "address": "شارع محمد محمود",
    "state_value": 3,
    "city_value": 150,
}
orders = [
    {
        "id": "rolex-gold-kod6-ZBasJJ",
        "color_id": "28-color-1",
        "quantity": 1,
        "price": 750,
        "commission": 250,
    },
        {
        "id": "rolex-gold-kod6-ZBasJJ",
        "color_id": "28-color-2",
        "quantity": 1,
        "price": 750,
        "commission": 250,
    },
]


# fekra = Fekra(
#     email="mosahsa040@gmail.com",
#     password="XeCZpnS98pWNdpM",
#     use_saved_cookies=False
# )


#fekra.make_order(customer_details=customer_information, orders=order_items)
