# 🤖 AI Personal Assistant

A beautiful, modern AI-powered personal assistant built with Semantic Kernel and FastAPI.

![Personal Assistant](https://img.shields.io/badge/AI-Personal%20Assistant-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi)

## ✨ Features

This assistant uses **real, live APIs** (no API keys required for external services):

| Feature | API | Description |
|---------|-----|-------------|
| 🌤️ **Weather** | wttr.in | Live weather data for any city worldwide |
| 💱 **Currency** | frankfurter.app | Real-time exchange rates (European Central Bank) |
| 🕐 **World Time** | worldtimeapi.org | Current time in 20+ major cities |
| 💭 **Quotes** | quotable.io | Inspirational quotes by category |
| 😄 **Jokes** | Official Joke API | Random jokes and programming humor |
| 📚 **Wikipedia** | Wikipedia API | Quick facts about any topic |
| 💰 **Finance** | Local calculations | Mortgages, investments, tips, bill splitting |
| 📋 **Tasks** | In-memory | Simple task management |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Azure OpenAI Service (with `az login` authentication)
- A `.env` file with your Azure OpenAI configuration

### 1. Install Dependencies

```bash
cd personal-assistant-app/backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend` folder (or use the existing one from code-samples):

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_CHAT_COMPLETION_MODEL=gpt-4o
AZURE_TENANT_ID=your-tenant-id  # Optional
```

### 3. Login to Azure

```bash
az login
```

### 4. Start the Backend Server

```bash
cd backend
python -m uvicorn app:app --reload --port 8000
```

### 5. Open the Frontend

Open `frontend/index.html` in your browser, or use a local server:

```bash
cd frontend
python -m http.server 3000
```

Then visit: http://localhost:3000

## 📁 Project Structure

```
personal-assistant-app/
├── backend/
│   ├── app.py              # FastAPI backend with Semantic Kernel
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # Beautiful dark theme styles
│   └── app.js              # Frontend JavaScript
└── README.md               # This file
```

## 💡 Example Queries

Try these queries with the assistant:

- "What's the weather in Paris and the current exchange rate EUR to USD?"
- "Tell me a joke and give me a motivational quote"
- "What time is it in London, Sydney, and Tokyo?"
- "Calculate monthly payments for a $300,000 mortgage at 6.5% for 30 years"
- "Tell me about the Eiffel Tower"
- "Convert 1000 USD to EUR, GBP, and JPY"

## 🎨 Screenshots

The app features a modern dark theme with:
- Gradient accents
- Smooth animations
- Responsive design
- Real-time API status indicator

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message to the assistant |
| `/api/health` | GET | Check API health status |
| `/api/capabilities` | GET | Get list of available capabilities |

## 📝 License

MIT License - Feel free to use and modify!

## 🙏 Credits

- **Semantic Kernel** - AI orchestration framework
- **FastAPI** - Modern Python web framework
- **wttr.in** - Weather data
- **frankfurter.app** - Currency exchange rates
- **worldtimeapi.org** - World time data
- **quotable.io** - Inspirational quotes
