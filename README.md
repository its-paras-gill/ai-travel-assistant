# AiTravelAssistant (Installation Guide)


### 1. Clone the Repository  
```bash
git clone https://github.com/its-paras-gill/ai-travel-assistant.git
cd ai-travel-assistant
```

### 2. Create config.py File 
```bash
nano config.py
```
Add API keys in it
```bash
GOOGLE_MAPS_API_KEY = ""
OPENAI_API_KEY = ""
OPENWEATHER_API_KEY = ""
```

### 3. Create and Activate a Virtual Environment (on Mac/Linux)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install googlemaps openai requests
```

### 5. Run the Application
```bash
python3 main.py
```

### 6. Deactivate the Virtual Environment
After you are done running your application, deactivate the virtual environment
```bash
deactivate
```

