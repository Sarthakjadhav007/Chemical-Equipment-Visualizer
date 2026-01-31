# Chemical Equipment Parameter Visualizer

A hybrid application (Web + Desktop) for visualizing chemical equipment data from CSV files.

## Project Structure
- `backend/`: Django REST API
- `frontend-web/`: React.js Dashboard
- `frontend-desktop/`: PyQt5 Desktop Application
- `data/`: Sample CSV for testing

## Tech Stack
- **Backend**: Django, Django REST Framework, Pandas, ReportLab
- **Frontend (Web)**: React, Chart.js, Tailwind CSS (via index.css), Lucide React
- **Frontend (Desktop)**: PyQt5, Matplotlib, Requests
- **Database**: SQLite

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
pip install django djangorestframework django-cors-headers pandas reportlab requests
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Web Setup
```bash
cd frontend-web
npm install
npm run dev
```

### 3. Frontend Desktop Setup
```bash
cd frontend-desktop
pip install PyQt5 matplotlib requests
python main.py
```

## Features
- **CSV Upload**: Upload `sample_equipment_data.csv` (found in `/data`) from either Web or Desktop.
- **Data Summary**: View total counts, averages, and type distributions.
- **Visualization**: Interactive charts (Pie and Bar).
- **History**: Access the last 5 uploaded datasets.
- **PDF Export**: Generate professional PDF reports for any dataset.

## Sample Data
Use the file located at `data/sample_equipment_data.csv` for initial testing.
