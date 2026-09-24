# 🚀 Deployment Guide — Fasal Saakshi

> 🌐 **Currently Live At:** [https://fasal-saakshi-crop-health.streamlit.app/](https://fasal-saakshi-crop-health.streamlit.app/)

This guide explains **how** and **where** to deploy your **Fasal Saakshi** application for free, step-by-step.

---

## 🎯 Best Places to Deploy

| Platform | Best For | Cost | Setup Time | Difficulty |
| :--- | :--- | :--- | :--- | :--- |
| **1. Streamlit Community Cloud** | **Recommended** (Native Streamlit hosting) | Free | ~5 min | 🟢 Easiest |
| **2. Hugging Face Spaces** | AI / Hackathon / Community demo | Free | ~5 min | 🟢 Very Easy |
| **3. Render.com** | Full web service hosting with custom domain | Free Tier | ~7 min | 🟡 Easy |
| **4. Docker (Cloud Run / VPS / Railway)** | Self-hosted or production containers | Pay-as-you-go | ~10 min | 🟠 Intermediate |

---

## 📋 Pre-requisite: Push Your Code to GitHub

All modern cloud deployment platforms pull your code from **GitHub**. If you haven't uploaded this folder to GitHub yet, follow these steps:

### Step 1: Initialize Git and Commit
Open PowerShell or your terminal in this project folder (`fasal-saakshi`):

```bash
git init
git add .
git commit -m "Initial commit: Fasal Saakshi ready for deployment"
```

*(Note: Your `.gitignore` automatically prevents your private `.streamlit/secrets.toml` or `.env` files from being committed).*

### Step 2: Create a GitHub Repository
1. Go to [github.com/new](https://github.com/new).
2. Name your repository (e.g., `fasal-saakshi`).
3. Set it to **Public** (required for free tiers on Streamlit Cloud & Hugging Face).
4. Click **Create repository** (do *not* initialize with README/license since you already have them).

### Step 3: Link and Push
Run the commands shown by GitHub (replace `<your-username>` with your GitHub username):

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/fasal-saakshi.git
git push -u origin main
```

---

## Option 1: Streamlit Community Cloud (⭐ Recommended)

Streamlit Community Cloud is built by the makers of Streamlit and offers zero-configuration hosting.

### Step-by-Step:
1. Go to **[share.streamlit.io](https://share.streamlit.io/)** and sign in with your GitHub account.
2. Click **"New app"** (or **"Create app"**).
3. Select your repository: `<your-username>/fasal-saakshi`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Click **"Advanced settings..."** (or go to App Settings ⚙️ -> **Secrets**):
   Paste your secret configuration in TOML format:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   ```
7. Click **"Deploy!"**.
8. Within 2–3 minutes, your live URL will be active at:
   `https://<your-app-name>.streamlit.app`

---

## Option 2: Hugging Face Spaces

Hugging Face Spaces is another popular, reliable, and completely free platform for AI web apps.

### Step-by-Step:
1. Go to **[huggingface.co/spaces](https://huggingface.co/spaces)** and sign up or log in.
2. Click **"Create new Space"**.
3. Fill in:
   - **Space name**: `fasal-saakshi`
   - **License**: Apache 2.0 or MIT
   - **Select the Space SDK**: Choose **Streamlit**
   - **Space hardware**: Free (CPU basic · 2 vCPU · 16 GB)
   - **Visibility**: Public
4. Click **Create Space**.
5. Go to **Settings** -> **Variables and secrets**:
   - Click **New secret**
   - Key: `GEMINI_API_KEY`
   - Value: `your-actual-gemini-api-key`
6. Push your files to the Hugging Face repository following their on-screen Git clone instructions, or link your GitHub repository.

---

## Option 3: Render (render.com)

Render provides free web service instances and supports our included `render.yaml` configuration out of the box.

### Step-by-Step:
1. Sign in at **[render.com](https://render.com/)** with GitHub.
2. Click **New +** -> **Web Service**.
3. Select **"Build and deploy from a Git repository"** and choose your `fasal-saakshi` repo.
4. Settings:
   - **Name**: `fasal-saakshi`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Instance Type**: Free
5. Under **Environment Variables**:
   - Add `GEMINI_API_KEY` = `your-actual-gemini-api-key`
   - Add `PYTHON_VERSION` = `3.11.9`
6. Click **Create Web Service**.

---

## Option 4: Docker / Google Cloud Run / VPS

A production-ready `Dockerfile` and `.dockerignore` are included in the project.

### Run locally or on any server with Docker:
```bash
# Build the Docker image
docker build -t fasal-saakshi .

# Run the container
docker run -p 8501:8501 -e GEMINI_API_KEY="your-key-here" fasal-saakshi
```
Access at `http://localhost:8501`.

### Deploy to Google Cloud Run:
```bash
gcloud run deploy fasal-saakshi \
  --source . \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your-key-here"
```

---

## ⚙️ Key Deployment Files Prepared

- **`.streamlit/config.toml`**: Configures headless mode, port binding, and disables telemetry.
- **`Procfile`**: Enables 1-click startup on PaaS hosts (Render, Railway, Heroku).
- **`runtime.txt`**: Pins Python 3.11 for guaranteed compatibility.
- **`Dockerfile` & `.dockerignore`**: Preconfigured container definition with health check.
- **`render.yaml`**: Infrastructure blueprint for Render.
- **`.gitignore`**: Shields secrets and API keys from accidental commits.
- **`.env.example`**: Reference for environment variables.
