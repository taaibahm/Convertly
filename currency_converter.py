import requests
import pytesseract
from PIL import Image
import re
import cv2
import time


API_KEY = 'cae1121bb98743a592755e21f4acc039'
BASE_URL = 'https://openexchangerates.org/api/latest.json'

def get_exchange_rates():
    response = requests.get(f"{BASE_URL}?app_id={API_KEY}")
    if response.status_code == 200:
        data = response.json()
        return data['rates']  # Return the exchange rates
    else:
        print("Error fetching data:", response.status_code)
        return None
    
def convert_currency(amount, from_currency, to_currency, rates):
    if from_currency not in rates or to_currency not in rates:
        print("Currency not found.")
        return None
    
    from_rate = rates[from_currency]

    to_rate = rates[to_currency]

    return (amount / from_rate) * to_rate

def extract_text_from_image(image_path):
    # Open the image using Pillow
    image = Image.open(image_path)
    
    # Use pytesseract to extract text
    text = pytesseract.image_to_string(image)
    return text

def extract_price_from_text(text):
    pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]#[0]  # Return the first found price
    return None

def process_frame(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
    _, thresh_frame = cv2.threshold(gray_frame, 150, 255, cv2.THRESH_BINARY)

    custom_config = r'--oem 3 --psm 6'
    extracted_text = pytesseract.image_to_string(thresh_frame, config=custom_config)

    price_value = extract_price_from_text(extracted_text)
    
    if price_value:
        print("Detected: ", price_value)
        return price_value
    return False
    #return price_value

def capture_camera():
    cap = cv2.VideoCapture(1)
    consec_count = 0
    last_price = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        price_found = process_frame(frame)

        if price_found:
            if price_found == last_price:
                consec_count += 1
            else:
                consec_count = 1
                last_price = price_found

            if consec_count == 3:
                print("Detected Price: ", price_found)
                # consec_count = 0
                break
        #    print("Stopping camera feed after detecting a price.")
        #    break

        cv2.imshow('Camera Feed', frame)

        if cv2.waitKey(2) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return price_found

    

if __name__ == "__main__":
    amount = float(capture_camera())
    rates = get_exchange_rates()
    if rates:
        from_currency = 'CAD'
        to_currency = 'INR'
        converted_amount = convert_currency(amount, from_currency, to_currency, rates)
        print(f"{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}")
