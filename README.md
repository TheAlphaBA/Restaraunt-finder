# 🍽️ AI-Powered Restaurant Recommendation System

An intelligent restaurant recommendation system powered by Zomato data and Google Gemini LLM. The system combines structured data filtering with AI-driven natural language recommendations to help users find their perfect dining spot.

## Features

- 🔍 Smart filtering by location, cuisine, budget, and rating
- 🤖 AI-powered recommendations using Google Gemini
- 📊 Real-world Zomato restaurant dataset from Hugging Face
- 🎯 Personalized explanations for each recommendation
- 🖥️ Interactive Streamlit web interface

## Project Structure

```
restaurant-recommendation/
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── input_handler.py         # User input validation & normalization
│   ├── data_loader.py           # Hugging Face dataset loader & caching
│   ├── preprocessor.py          # Data cleaning & normalization
│   ├── filter_engine.py         # Restaurant filtering logic
│   ├── prompt_builder.py        # LLM prompt construction
│   ├── llm_client.py            # LLM API wrapper (Gemini / OpenAI)
│   ├── output_formatter.py      # Parse & structure LLM response
│   └── models.py                # Dataclasses: UserPreferences, RecommendationCard
├── config/
│   └── config.yaml              # Model settings, budget thresholds
├── tests/
│   ├── test_filter_engine.py
│   ├── test_prompt_builder.py
│   └── test_output_formatter.py
├── Doc/
│   ├── ProblemStatement.md
│   ├── architecture.md
│   └── implementation-plan.md
├── requirements.txt
├── .env                         # API keys (never commit)
├── .gitignore
└── README.md
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Edit `.env` and add your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the App Locally

```bash
streamlit run app/main.py
```

## Deployment

### Option A — Streamlit Cloud (Recommended)

1. Push this repository to GitHub (ensure `.env` is **not** committed).
2. Visit [share.streamlit.io](https://share.streamlit.io) and connect your GitHub repository.
3. In the Streamlit Cloud dashboard, go to the app settings and configure your **Secrets**:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
4. Deploy — your app will be assigned a public URL automatically.

### Option B — Docker

Build and run the app via Docker:

```bash
# Build the image
docker build -t restaurant-recommender .

# Run the container
docker run -p 8501:8501 --env-file .env restaurant-recommender
```

## Dataset

Uses the [Zomato Restaurant Recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) dataset from Hugging Face.

## Architecture

See [Doc/architecture.md](Doc/architecture.md) for the full system architecture.

## Implementation Plan

See [Doc/implementation-plan.md](Doc/implementation-plan.md) for the phase-wise build plan.
