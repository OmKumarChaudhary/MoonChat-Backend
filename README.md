---
title: MoonChat Backend
emoji: 🌙
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# MoonChat Backend

This is the Flask backend for the MoonChat application, containerized for Hugging Face Spaces.

## Architecture

- **Framework**: Flask
- **Machine Learning**: TensorFlow (CPU), NLTK, Scikit-learn
- **Data Source**: PyCoinGecko for real-time crypto prices
- **Deployment**: Docker SDK on Hugging Face Spaces

## API Endpoints

- `/`: Home check
- `/api/crypto`: Crypto-related routes
- `/api/chatbot`: Chatbot interaction routes

## Local Development (Docker)

To run this backend locally using Docker:

```bash
docker build -t moonchat-backend .
docker run -p 7860:7860 moonchat-backend
```
