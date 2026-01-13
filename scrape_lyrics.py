import json
import logging
import os
import re
import time

import lyricsgenius
from dotenv import load_dotenv

# Suppress lyricsgenius logging
logging.getLogger("lyricsgenius").setLevel(logging.ERROR)

DB_FILE = "yeat_lyrics.txt"
PROGRESS_FILE = "scrape_progress.json"

load_dotenv()

def clean_lyrics(lyrics):
    lyrics = re.sub(r'\d*Embed$', '', lyrics)
    return lyrics.strip()

def load_progress():
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except Exception as e:
        print(f"✗ Could not read progress file: {e}")
        return set()

def save_progress(processed_urls):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(processed_urls), f)
    except Exception as e:
        print(f"✗ Could not save progress file: {e}")

def append_to_db(filename, song_title, lyrics):
    """Write each song to the database immediately"""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"<|startoftext|>\n{lyrics}\n<|endoftext|>\n")
        f.flush()
    print(f"✓ Saved: {song_title}")

def scrape_yeat_lyrics():
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        print("Error: GENIUS_ACCESS_TOKEN not found in environment variables.")
        return

    genius = lyricsgenius.Genius(token, timeout=30, retries=5, remove_section_headers=True, verbose=False)
    
    genius.excluded_terms = ["(Remix)", "(Live)"]
    genius.skip_non_songs = True

    processed_urls = load_progress()
    
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write("")

    try:
        print("Searching for Yeat on Genius...")
        artist = genius.search_artist("Yeat", sort="popularity", max_songs=400, per_page=50)
        
        if not artist:
            print("✗ Could not find artist")
            return
            
        print(f"✓ Found {artist.name} with {len(artist.songs)} songs")
        print(f"Starting scrape (resuming from {len(processed_urls)} saved)...\n")
        
        song_count = len(processed_urls)
        songs_list = list(artist.songs)
        
        for idx, song in enumerate(songs_list, 1):
            song_url = song.url if hasattr(song, 'url') else song.title
            status = f"[{idx}/{len(songs_list)}] {song.title}"
            
            if song_url in processed_urls:
                print(f"{status} → already saved")
                continue
            
            print(status, end=" → ", flush=True)
            
            try:
                full_song = genius.song(song.url) if hasattr(song, 'url') else genius.song(song.title)
                
                if full_song and full_song.lyrics:
                    cleaned = clean_lyrics(full_song.lyrics)
                    if len(cleaned) > 50:
                        append_to_db(DB_FILE, full_song.title, cleaned)
                        processed_urls.add(song_url)
                        song_count += 1
                        if song_count % 5 == 0:
                            save_progress(processed_urls)
                    else:
                        print("too short")
                else:
                    print("no lyrics")
                    
            except KeyboardInterrupt:
                print("\n\n✗ Interrupted by user")
                save_progress(processed_urls)
                return
            except Exception as e:
                print(f"error: {type(e).__name__}")
                time.sleep(1)
                continue
                
            time.sleep(0.2)
        
        save_progress(processed_urls)
        print(f"\n✓ Done! Total songs saved: {song_count}")
            
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user. Progress saved.")
        save_progress(processed_urls)
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        save_progress(processed_urls)
        print("Partial lyrics may have been saved to yeat_lyrics.txt")

if __name__ == "__main__":
    scrape_yeat_lyrics()
