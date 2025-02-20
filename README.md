# Medical Form OCR Data Extractor

An intelligent OCR (Optical Character Recognition) system designed to extract and process data from medical forms, capable of handling both printed and handwritten text with various label formats.

## 🌟 Features

- **Dual OCR Processing**: Combines Tesseract OCR and EasyOCR for optimal text recognition
- **Smart Label Recognition**: Handles multiple variations of field labels
- **Handwriting Support**: Specialized processing for handwritten text
- **Advanced Image Preprocessing**: Multiple preprocessing techniques for improved accuracy
- **Structured Data Output**: Converts extracted text to structured JSON format
- **MySQL Integration**: Automatic storage of extracted data in a MySQL database
- **Flexible Pattern Matching**: Supports various form layouts and label formats

## 🚀 Getting Started

### Prerequisites

```bash
# Required Python version
Python 3.7+
```

### System Dependencies

Before installing the Python packages, ensure you have the following system dependencies:

```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libmysqlclient-dev \
    python3-opencv

# For MacOS
brew install tesseract
brew install mysql-connector-c
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/VIVEKREDDYGOLLALA/Oaksol.git
cd Oaksol
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Unix/MacOS
# OR
.\venv\Scripts\activate  # For Windows
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### Configuration

1. Update MySQL connection details in the code:
```python
conn = mysql.connector.connect(
    host="your_host",
    user="your_user",
    password="your_password"
)
```

2. Ensure your image directory structure is set up:
```
project_root/
├── images/
│   └── image.png
├── ocr.py
└── requirements.txt
```

## 📚 Usage

1. Place your medical form images in the `images` directory
2. Run the script:
```bash
python ocr.py
```

3. The script will:
   - Process the image using multiple OCR methods
   - Extract structured data
   - Store the results in MySQL database

## 📋 Supported Fields

The system recognizes various formats for the following fields:

### Basic Information
- Patient Name (variations: Name, Full Name, Patient)
- Date of Birth (variations: DOB, Birth Date)
- Visit Date (variations: Date, Appointment Date)

### Medical Measurements
- Blood Pressure (variations: BP, Pressure)
- Heart Rate (variations: HR, Pulse, BPM)
- Temperature (variations: Temp, Body Temperature)
- SPO2 (variations: Oxygen Saturation, O2 Sat)
- Weight (variations: Wt, Mass)
- Height (variations: Ht, Tall)
- Blood Glucose (variations: BG, Sugar, Glucose)
- Respirations (variations: Resp Rate, RR, Breathing Rate)

### Treatment Information
- Injection (variations: Shot, Received Injection)
- Exercise Therapy (variations: Physical Therapy, PT)

### Patient Assessment
- Pain Levels
- Difficulty Ratings
- Progress Tracking

## 🗄️ Database Structure

The system creates two main tables:

1. `patients` table:
```sql
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    dob DATE NULL
);
```

2. `forms_data` table:
```sql
CREATE TABLE forms_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    form_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

## 📦 Dependencies

```txt
pytesseract>=0.3.8
opencv-python>=4.5.3
easyocr>=1.4
mysql-connector-python>=8.0
Pillow>=8.3.2
numpy>=1.21.2
```

## 🛠️ Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## ⚠️ Known Limitations

- Requires good image quality for optimal results
- Handwriting recognition accuracy depends on clarity
- Form layout should be relatively consistent
- MySQL connection details are hardcoded (future enhancement planned)


## 🙏 Acknowledgments

- OpenCV community for image processing tools
- Tesseract OCR team
- EasyOCR developers
- All contributors who help improve this project

## 📞 Support

For support, email gollalavivek@email.com or create an issue in the repository.
