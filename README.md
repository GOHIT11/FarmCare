# 🌾 MandiPredict - Smart Agricultural Price Forecasting

**MandiPredict** is an AI-powered application designed to empower Indian farmers by providing accurate, real-time market price predictions for their crops. 

By combining historical data analysis with machine learning, MandiPredict helps farmers make informed decisions about **when** and **where** to sell their produce to maximize profits. It also features a Generative AI assistant to answer farming-related queries in local languages.

## ✨ Key Features

*   **📈 Price Prediction**: Uses Machine Learning (Random Forest/Gradient Boosting) to forecast crop prices for the next 7 days based on historical trends and weather patterns.
*   **🤖 AI Kisan Sahayak**: A built-in chatbot powered by **Google Gemini AI** that answers farmers' questions about crop diseases, fertilizers, and techniques in **Hindi, Telugu, and English**.
*   **📍 Mandi Optimization**: unique logic that calculates the "Best Mandi to Sell" by analyzing current prices, transport costs, and storage costs to recommend the most profitable option.
*   **🌦️ Weather Integration**: Real-time 10-day weather forecasts to help plan harvesting and storage.
*   **📊 Interactive Dashboard**: Visual graphs and charts (Line & Bar) to track price trends easily.
*   **📱 Multi-Language Support**: Designed to be accessible to farmers across different regions.

## 🛠️ Technology Stack

This project is built using a robust modern tech stack:

### **Mobile App (Frontend)**
*   **Framework**: [Flutter](https://flutter.dev/) (Dart) - for a beautiful, native cross-platform experience.
*   **State Management**: Provider / Riverpod.
*   **Charts**: `fl_chart` for visualizing price trends.
*   **HTTP**: `dio` / `http` for API communication.

### **Backend & AI**
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python) - High-performance backend.
*   **Machine Learning**: `scikit-learn`, `pandas`, `numpy`, `joblib`.
*   **GenAI**: **Google Gemini 1.5 Flash** for the conversational assistant.
*   **Data Source**: Scraping capabilities for **Agmarknet** (Government of India) data.

## 🚀 Getting Started

### Prerequisites
*   Flutter SDK installed.
*   Python 3.9+ installed.

### 1. Backend Setup
The backend powers the predictions and AI features.

```bash
cd backend
# Create virtual environment
python -m venv venv
# Activate it (Windows)
.\venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Run the server
uvicorn main:app --reload --host 0.0.0.0
```

> **Note**: The repository includes a "Smart Fallback" mode. If real historical data is missing (due to GitHub file size limits), the app generates realistic mock data so you can test the UI and flow immediately.

### 2. Mobile App Setup
```bash
# Get dependencies
flutter pub get
# Run the app
flutter run
```

## 📸 Screenshots
*(Add screenshots of your app Dashboard, Prediction Screen, and Chatbot here)*

## 🤝 Contribution
Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License
This project is open-source and available under the MIT License.
