import argparse
import json
import logging
import os
import re
import sys
import time

import lyricsgenius
from dotenv import load_dotenv

logging.getLogger("lyricsgenius").setLevel(logging.WARNING)

DB_FILE = "yeat_lyrics.txt"
PROGRESS_FILE = "scrape_progress.json"

load_dotenv()


def clean_lyrics(lyrics: str) -> str:
    """Clean and normalize lyrics text."""
    cleaned = re.sub(r"\d*Embed$", "", lyrics)
    return cleaned.strip()


def load_progress() -> set[int]:
    """Return the set of song IDs we have already saved."""
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError:
        print("[PROGRESS] Starting fresh (no existing progress file)")
        return set()
    except Exception as exc:
        print(f"[PROGRESS] Could not read progress file: {exc}")
        return set()

    ids: set[int] = set()
    for entry in raw:
        try:
            ids.add(int(entry))
        except (TypeError, ValueError):
            continue

    # If progress claims songs were saved but the DB file is empty, reset.
    if ids and (not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0):
        print("[PROGRESS] Progress file found but lyrics store is empty. Resetting saved list.")
        return set()

    print(f"[PROGRESS] Loaded {len(ids)} saved song IDs")
    return ids


def save_progress(saved_ids: set[int]) -> None:
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as handle:
            json.dump(sorted(saved_ids), handle)
        print(f"[PROGRESS SAVED] {len(saved_ids)} songs")
    except Exception as exc:
        print(f"[PROGRESS] Failed to save progress: {exc}")


def append_to_db(song_title: str, lyrics: str) -> bool:
    """Append a song's lyrics to the datastore."""
    try:
        with open(DB_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"<|startoftext|>\n{lyrics}\n<|endoftext|>\n")
            handle.flush()
        print(f"  ✓ Stored lyrics for: {song_title}")
        return True
    except Exception as exc:
        print(f"  [DB] Failed to write lyrics: {exc}")
        return False


def ensure_datastore_exists() -> None:
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as handle:
            handle.write("")
        print(f"[INIT] Created lyrics store at {DB_FILE}")


def scrape_yeat_lyrics(max_songs: int = 400, per_page: int = 50, limit: int | None = None) -> None:
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        print("[ERROR] GENIUS_ACCESS_TOKEN not found in environment.")
        return

    try:
        genius = lyricsgenius.Genius(
            token,
            timeout=30,
            retries=5,
            remove_section_headers=True,
            verbose=False,
        )
    except Exception as exc:
        print(f"[ERROR] Unable to create Genius client: {exc}")
        return

    genius.excluded_terms = ["(Remix)", "(Live)"]
    genius.skip_non_songs = True

    ensure_datastore_exists()
    saved_ids = load_progress()
    total_saved_before = len(saved_ids)
    new_saves = 0

    target_total = limit if limit is not None else max_songs
    
    try:
        print("[SEARCH] Finding Yeat's ID...")
        artist_search = genius.search_artists("Yeat")
        if not artist_search or not artist_search['sections'][0]['hits']:
            print("[ERROR] Could not find artist Yeat")
            return
        
        artist_id = artist_search['sections'][0]['hits'][0]['result']['id']
        artist_name = artist_search['sections'][0]['hits'][0]['result']['name']
        print(f"[SEARCH] ✓ Found {artist_name} (ID: {artist_id})")
        print(f"[SCRAPE] Processing lyrics page-by-page (Target: {target_total} songs)...\n")

        page = 1
        processed_count = 0
        
        while processed_count < target_total:
            res = genius.artist_songs(artist_id, sort="popularity", per_page=per_page, page=page)
            songs = res['songs']
            if not songs:
                break
            
            for song_data in songs:
                if processed_count >= target_total:
                    break
                
                processed_count += 1
                song_id = song_data['id']
                song_title = song_data['title']

                status = f"[{processed_count:3d}/{target_total}] {song_title}"
                
                if song_id in saved_ids:
                    print(f"{status} → SKIP (already saved)")
                    continue

                print(f"{status} → retrieving lyrics", end=" ", flush=True)

                try:
                    # Get lyrics directly for the ID
                    lyrics_text = genius.lyrics(song_id=song_id)
                    if not lyrics_text:
                        print("→ FAIL (no lyrics)")
                        continue

                    cleaned = clean_lyrics(lyrics_text)
                    if len(cleaned) < 50:
                        print("→ SKIP (too short)")
                        continue

                    if append_to_db_silent(song_title, cleaned):
                        saved_ids.add(song_id)
                        new_saves += 1
                        print("→ ✓ SAVED")
                        if (total_saved_before + new_saves) % 5 == 0:
                            save_progress(saved_ids)
                    
                except Exception as exc:
                    print(f"→ ERROR: {exc}")
                
                time.sleep(0.2)

            page = res['next_page']
            if not page:
                break
                
    except KeyboardInterrupt:
        print("\n[INTERRUPT] User interrupted. Saving progress...")
    except Exception as exc:
        print(f"[ERROR] Scrape failed: {exc}")

    if new_saves:
        save_progress(saved_ids)

    print(f"\n[SUMMARY] Saved {new_saves} new song(s). Total in DB: {len(saved_ids)}")

def append_to_db_silent(song_title: str, lyrics: str) -> bool:
    """Append a song's lyrics to the datastore without extra printing."""
    try:
        with open(DB_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"<|startoftext|>\n{lyrics}\n<|endoftext|>\n")
            handle.flush()
        return True
    except Exception:
        return False



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Yeat lyrics from Genius")
    parser.add_argument("--max-songs", type=int, default=400, help="Maximum songs to fetch from Genius")
    parser.add_argument("--per-page", type=int, default=50, help="Songs per page when querying Genius")
    parser.add_argument("--limit", type=int, help="Process only the first N songs (for smoke tests)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    scrape_yeat_lyrics(max_songs=args.max_songs, per_page=args.per_page, limit=args.limit)

