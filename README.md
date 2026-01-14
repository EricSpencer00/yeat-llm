# 🚜 Yeat-LLM (TwizzyBot)

The easiest way to make your own Yeat songs and talk to the Geeker.

## 🚀 How to use
1. **Open** a terminal in this folder.
2. **Run** these simple commands:

```bash
# Install everything
pip install -r requirements.txt

# Download lyrics
python3 scrape_lyrics.py

# Train the AI
python3 train_model.py

# Chat with Yeat!
python3 yeat_bot.py
```

## 📦 Making it an App (.exe / .app)
If you want to turn this into a single clickable file to share with friends, run:
```bash
pyinstaller --onefile --add-data "yeat_model:yeat_model" yeat_bot.py
```
Look inside the `dist` folder for your app!

## ⚠️ Requirements
- You need a Genius API Token in the `.env` file.
