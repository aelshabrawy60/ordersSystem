


def extractProductInfo(fekraUrl, easyOrdersUrl):
    return


import requests
from bs4 import BeautifulSoup

def extractEasyOrdersProduct(easyOrdersUrl: str):
    result = {
        "easy_order_id": None,
        "price": None,
        "colors": []
    }
    
    try:
        # Fetch page
        response = requests.get(easyOrdersUrl, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Product name
        name_tag = soup.find("h1", class_="product_name")
        if name_tag:
            result["easy_order_id"] = name_tag.get_text(strip=True)

        # Price
        price_tag = soup.find("p", id="sale-price")
        if price_tag:
            result["price"] = price_tag.get_text(strip=True)

        # Colors (fix: look for p.sr-only inside any color option)
        color_tags = soup.select("div[role='radio'] p.sr-only")
        print(color_tags)

        colors = [tag.get_text(strip=True) for tag in color_tags if tag]
        result["colors"] = colors

    except Exception as e:
        print(f"Error scraping {easyOrdersUrl}: {e}")

    return result




def extractFekraProudct(easyOrdersUrl, colors):
    return


# Example usage
if __name__ == "__main__":
    url = "https://pretful.com/products/TISSOTCouturierChronograph"
    data = extractEasyOrdersProduct(url)
    print(data)