# Mandi Price Prediction Backend

## Setup

1. Navigate to `backend` folder.
2. Create virtual environment (optional): `python -m venv venv`
3. Activate venv: `.\venv\Scripts\activate` (Windows)
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create `.env` file (optional) with `OPENWEATHER_API_KEY=your_key` if you want real weather data.

## Running

Start the server:

```bash
uvicorn main:app --reload
```

## Endpoints

- `GET /health`
- `GET /options`
- `POST /predict` body: `{"mandi": "Lasalgaon", "commodity": "Onion"}`

## Training

Models are trained automatically on startup if not found. To retrain, delete the `models/` directory and restart.
