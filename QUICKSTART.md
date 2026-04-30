# Quick Start - ScholarEval ⚡

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- pip
- Mistral API key (get one at https://mistral.ai)

## Setup (2 minutes)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API key
```bash
# Copy example config
cp .env.example .env

# Edit .env and add your Mistral API key
# MISTRAL_API_KEY=sk-xxxxxxxxxxxxx
```

## Run (30 seconds)

```bash
python main.py
```

Visit: **http://localhost:8000**

## Usage (2 minutes)

### Step 1: Upload Reference PDF
- Click "📄 Upload Reference PDF"
- Select a PDF file (textbook chapter, study guide, etc.)
- Click "Upload PDF"
- Wait for ✅ success message

### Step 2: Evaluate Answer
- Enter a **question** from the PDF
- Enter the **student's answer**
- (Optional) Set max marks
- Click "Evaluate Answer"
- View the AI evaluation

## Example

**Question:** What is photosynthesis?

**Student Answer:** A process where plants use sunlight and water to create glucose and oxygen.

**Result:**
```
Score: 5/5
Feedback: Perfect answer covering all key points
✅ Correctly mentioned: sunlight, water, glucose, oxygen
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "MISTRAL_API_KEY not set" | Add your key to `.env` file |
| "No PDF uploaded" | Upload a PDF first before evaluating |
| "Connection error" | Ensure server is running (`python main.py`) |

## Next Steps

- 📖 Read [README.md](README.md) for full documentation
- 🚀 See [Deployment Guide](DEPLOYMENT.md) for production setup
- 🔧 Check config options in [config.py](backend/core/config.py)

## Stop Server

Press `Ctrl+C` in terminal

---

That's it! 🎉 Your AI evaluation system is ready to use.
