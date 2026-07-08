# IDBI WealthAI - Backend

The backend service powering the IDBI WealthAI dashboard. Built with FastAPI, this application provides robust RESTful APIs to handle customer data fetching, financial portfolio analysis, and powers the intelligent AI Financial Coach via LLM integrations.

## Features

- **AI LLM Gateway**: Connects directly to OpenRouter API (Claude 3.5 Sonnet / Llama 3) to generate intelligent financial insights and converse with the user.
- **SQLite Chat History**: Maintains context-aware conversation history for the AI Financial Coach.
- **Customer Data Service**: Serves structured mock data for customer portfolios, health scores, and financial planning goals.
- **CORS Configured**: Ready to safely interface with the React frontend.

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: SQLite (for chat history) & JSON (for mock customer data)
- **LLM Integration**: OpenAI Python SDK (via OpenRouter)
- **Server**: Uvicorn

## Getting Started

### Prerequisites

- Python 3.9+
- An OpenRouter API Key (for the AI Coach functionality)

### Installation & Setup

1. **Clone the repository**:
   Navigate to the backend folder.

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the `app/` directory (or copy `.env.example`) and add your OpenRouter API Key:
   ```env
   OPENROUTER_API_KEY="your-api-key-here"
   ```
   *(Note: Never commit your `.env` file to version control!)*

5. **Run the Development Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. You can view the automatic Swagger UI documentation at `http://localhost:8000/docs`.

---
*Developed for the IDBI WealthAI Project.*
