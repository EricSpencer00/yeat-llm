# Yeat LLM

This project scrapes Yeat lyrics from Genius and trains a small Language Model (GPT-2) to generate new songs in his style.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **API Key**:
    The `.env` file contains the Genius API Token. 
    *Note: The token provided initially seems to be invalid/expired. Please generate a new Client Access Token from [Genius API Clients](https://genius.com/api-clients) and update the `.env` file.*

## Usage

1.  **Scrape Lyrics**:
    Run the scraper to download lyrics into `yeat_lyrics.txt`.
    ```bash
    python scrape_lyrics.py
    ```

2.  **Train & Generate**:
    Run the training script to fine-tune GPT-2 and generate text.
    ```bash
    python train_and_generate.py
    ```
    *Note: Training may take some time depending on your hardware.*
