import pytesseract
import cv2
import json
import re
import mysql.connector
from PIL import Image
import easyocr

class TextExtractor:
    def __init__(self):
        # Initialize OCR readers
        self.reader = easyocr.Reader(['en'])  # For handwritten text
        
        # Define variations of field labels
        self.field_variations = {
            "patient_name": [
                r"(?:Patient\s*)?Name[:\s]+([A-Za-z\s]+)",
                r"Full\s*Name[:\s]+([A-Za-z\s]+)",
                r"Patient[:\s]+([A-Za-z\s]+)"
            ],
            "dob": [
                r"(?:Date\s*of\s*Birth|DOB|Birth\s*Date)[:\s]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
                r"Born[:\s]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})"
            ],
            "date": [
                r"(?:Date|Visit\s*Date|Appointment\s*Date)[:\s]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
                r"(?:Today's\s*Date)[:\s]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})"
            ],
            "injection": [
                r"(?:Injection|Shot)[:\s]+(Yes|No|Y|N)",
                r"(?:Received\s*Injection)[:\s]+(Yes|No|Y|N)"
            ],
            "exercise_therapy": [
                r"(?:Exercise\s*Therapy|Physical\s*Therapy|PT)[:\s]+(Yes|No|Y|N)",
                r"(?:Exercise\s*Program)[:\s]+(Yes|No|Y|N)"
            ],
            "blood_pressure": [
                r"(?:Blood\s*Pressure|BP)[:\s]+(\d{2,3}/\d{2,3})",
                r"(?:Pressure)[:\s]+(\d{2,3}/\d{2,3})"
            ],
            "heart_rate": [
                r"(?:Heart\s*Rate|HR|Pulse)[:\s]+(\d+)",
                r"(?:BPM)[:\s]+(\d+)"
            ],
            "weight": [
                r"(?:Weight|Wt)[:\s]+(\d+)",
                r"(?:Mass)[:\s]+(\d+)"
            ],
            "height": [
                r"(?:Height|Ht)[:\s]+([\d']+\s?[\d\"]?)",
                r"(?:Tall)[:\s]+([\d']+\s?[\d\"]?)"
            ],
            "spo2": [
                r"(?:SPO2|Oxygen\s*Saturation|O2\s*Sat)[:\s]+(\d+)",
                r"(?:Oxygen)[:\s]+(\d+)"
            ],
            "temperature": [
                r"(?:Temperature|Temp)[:\s]+([\d.]+)",
                r"(?:Body\s*Temperature)[:\s]+([\d.]+)"
            ],
            "blood_glucose": [
                r"(?:Blood\s*Glucose|BG|Sugar)[:\s]+(\d+)",
                r"(?:Glucose)[:\s]+(\d+)"
            ],
            "respirations": [
                r"(?:Respirations|Resp\s*Rate|RR)[:\s]+(\d+)",
                r"(?:Breathing\s*Rate)[:\s]+(\d+)"
            ]
        }

        # Define variations for difficulty ratings
        self.difficulty_variations = {
            "bending": [
                r"(?:Bending|Bend)[:\s]+(\d+)",
                r"(?:Flexibility)[:\s]+(\d+)"
            ],
            "putting_on_shoes": [
                r"(?:Putting\s*on\s*Shoes|Shoes)[:\s]+(\d+)",
                r"(?:Footwear)[:\s]+(\d+)"
            ],
            "sleeping": [
                r"(?:Sleeping|Sleep\s*Quality)[:\s]+(\d+)",
                r"(?:Rest)[:\s]+(\d+)"
            ]
        }

        # Define variations for pain symptoms
        self.pain_variations = {
            "pain": [
                r"(?:Pain|Pain\s*Level)[:\s]+(\d+)",
                r"(?:Discomfort)[:\s]+(\d+)"
            ],
            "numbness": [
                r"(?:Numbness|Numb)[:\s]+(\d+)",
                r"(?:Loss\s*of\s*Feeling)[:\s]+(\d+)"
            ],
            "tingling": [
                r"(?:Tingling|Pins\s*and\s*Needles)[:\s]+(\d+)",
                r"(?:Prickling)[:\s]+(\d+)"
            ],
            "burning": [
                r"(?:Burning|Burn)[:\s]+(\d+)",
                r"(?:Hot\s*Sensation)[:\s]+(\d+)"
            ],
            "tightness": [
                r"(?:Tightness|Tight)[:\s]+(\d+)",
                r"(?:Stiffness)[:\s]+(\d+)"
            ]
        }

    def preprocess_image(self, image_path):
        image = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return {
            'original': image,
            'gray': gray,
            'thresh': thresh,
            'denoised': denoised,
            'enhanced': enhanced
        }

    def extract_text(self, image_path):
        # Process image
        processed_images = self.preprocess_image(image_path)
        
        # Extract text using multiple methods
        texts = []
        
        # Try Tesseract OCR with different preprocessed images
        for img_type, img in processed_images.items():
            if img_type != 'original':  # Skip original colored image
                text = pytesseract.image_to_string(img, lang='eng')
                texts.append(text)
        
        # Try EasyOCR for handwritten text
        handwritten_results = self.reader.readtext(processed_images['enhanced'])
        handwritten_text = ' '.join([result[1] for result in handwritten_results])
        texts.append(handwritten_text)
        
        # Combine all extracted text
        combined_text = ' '.join(texts)
        return combined_text

    def find_match(self, text, patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Normalize Yes/No answers
                if value.upper() in ['Y', 'YES']:
                    return 'Yes'
                elif value.upper() in ['N', 'NO']:
                    return 'No'
                return value
        return "Unknown"

    def extract_data(self, text):
        extracted_data = {}

        # Extract basic fields
        for field, patterns in self.field_variations.items():
            extracted_data[field] = self.find_match(text, patterns)

        # Extract difficulty ratings
        extracted_data["difficulty_ratings"] = {}
        for difficulty, patterns in self.difficulty_variations.items():
            value = self.find_match(text, patterns)
            extracted_data["difficulty_ratings"][difficulty] = int(value) if value.isdigit() else 0

        # Extract pain symptoms
        extracted_data["pain_symptoms"] = {}
        for pain, patterns in self.pain_variations.items():
            value = self.find_match(text, patterns)
            extracted_data["pain_symptoms"][pain] = int(value) if value.isdigit() else 0

        # Extract patient changes (keeping the original structure)
        patient_changes_patterns = {
            "since_last_treatment": r"Since Last Treatment[:\s]+([\w\s]+)",
            "since_start_of_treatment": r"Since Start of Treatment[:\s]+([\w\s]+)",
            "last_3_days": r"Last 3 Days[:\s]+([\w\s]+)"
        }
        
        extracted_data["patient_changes"] = {
            key: self.find_match(text, [pattern]) 
            for key, pattern in patient_changes_patterns.items()
        }

        # Structure medical assistant data
        extracted_data["medical_assistant_data"] = {
            "blood_pressure": extracted_data.pop("blood_pressure"),
            "hr": extracted_data.pop("heart_rate"),
            "weight": extracted_data.pop("weight"),
            "height": extracted_data.pop("height"),
            "spo2": extracted_data.pop("spo2"),
            "temperature": extracted_data.pop("temperature"),
            "blood_glucose": extracted_data.pop("blood_glucose"),
            "respirations": extracted_data.pop("respirations")
        }

        return json.dumps(extracted_data)

def store_in_mysql(json_data):
    try:
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        patient_name = json_data["patient_name"] if json_data["patient_name"].strip() else None
        dob = json_data["dob"] if json_data["dob"] != "Unknown" else None
        date = json_data["date"] if json_data["date"] != "Unknown" else None
        injection = json_data["injection"] if json_data["injection"] != "Unknown" else None
        exercise_therapy = json_data["exercise_therapy"] if json_data["exercise_therapy"] != "Unknown" else None
        
        difficulty_ratings = {
            "bending": json_data["difficulty_ratings"]["bending"] if json_data["difficulty_ratings"]["bending"] != "Unknown" else 0,
            "putting_on_shoes": json_data["difficulty_ratings"]["putting_on_shoes"] if json_data["difficulty_ratings"]["putting_on_shoes"] != "Unknown" else 0,
            "sleeping": json_data["difficulty_ratings"]["sleeping"] if json_data["difficulty_ratings"]["sleeping"] != "Unknown" else 0
        }

        patient_changes = {
            "since_last_treatment": json_data["patient_changes"]["since_last_treatment"] if json_data["patient_changes"]["since_last_treatment"] != "Unknown" else None,
            "since_start_of_treatment": json_data["patient_changes"]["since_start_of_treatment"] if json_data["patient_changes"]["since_start_of_treatment"] != "Unknown" else None,
            "last_3_days": json_data["patient_changes"]["last_3_days"] if json_data["patient_changes"]["last_3_days"] != "Unknown" else None
        }

        pain_symptoms = {
            "pain": json_data["pain_symptoms"]["pain"] if json_data["pain_symptoms"]["pain"] != "Unknown" else 0,
            "numbness": json_data["pain_symptoms"]["numbness"] if json_data["pain_symptoms"]["numbness"] != "Unknown" else 0,
            "tingling": json_data["pain_symptoms"]["tingling"] if json_data["pain_symptoms"]["tingling"] != "Unknown" else 0,
            "burning": json_data["pain_symptoms"]["burning"] if json_data["pain_symptoms"]["burning"] != "Unknown" else 0,
            "tightness": json_data["pain_symptoms"]["tightness"] if json_data["pain_symptoms"]["tightness"] != "Unknown" else 0
        }

        medical_assistant_data = {
            "blood_pressure": json_data["medical_assistant_data"]["blood_pressure"] if json_data["medical_assistant_data"]["blood_pressure"] != "Unknown" else None,
            "hr": json_data["medical_assistant_data"]["hr"] if json_data["medical_assistant_data"]["hr"] != "Unknown" else None,
            "weight": json_data["medical_assistant_data"]["weight"] if json_data["medical_assistant_data"]["weight"] != "Unknown" else None,
            "height": json_data["medical_assistant_data"]["height"] if json_data["medical_assistant_data"]["height"] != "Unknown" else None,
            "spo2": json_data["medical_assistant_data"]["spo2"] if json_data["medical_assistant_data"]["spo2"] != "Unknown" else None,
            "temperature": json_data["medical_assistant_data"]["temperature"] if json_data["medical_assistant_data"]["temperature"] != "Unknown" else None,
            "blood_glucose": json_data["medical_assistant_data"]["blood_glucose"] if json_data["medical_assistant_data"]["blood_glucose"] != "Unknown" else None,
            "respirations": json_data["medical_assistant_data"]["respirations"] if json_data["medical_assistant_data"]["respirations"] != "Unknown" else None
        }

        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Vivekreddy1234*"
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS Oaksol;")
        cursor.execute("USE Oaksol;")

        # Create tables if not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                dob DATE NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forms_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT,
                form_json JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            );
        """)

        # Insert patient data
        cursor.execute("INSERT INTO patients (name, dob) VALUES (%s, %s)", 
                       (patient_name, dob))
        patient_id = cursor.lastrowid

        # Insert extracted JSON data
        cursor.execute("INSERT INTO forms_data (patient_id, form_json) VALUES (%s, %s)", 
                       (patient_id, json.dumps(json_data)))

        conn.commit()
        print("Data inserted successfully into MySQL!")

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

    except Exception as e:
        print(f"Unexpected Error: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    extractor = TextExtractor()
    image_path = 'images/image copy 2.png'
    extracted_text = extractor.extract_text(image_path)
    json_data = extractor.extract_data(extracted_text)
    print(json_data)
    store_in_mysql(json_data)

if __name__ == "__main__":
    main()