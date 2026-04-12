"""
Watch OpenAI prompts in real-time.
Run in a separate terminal:  python watch_prompts.py
Press Ctrl+C to stop.
"""
import os, time, sys

LOG_FILE = os.path.join(os.path.dirname(__file__), "prompt_log.txt")

def main():
    # Create / truncate the log file so we start fresh
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    print(f"👀 Watching prompts in: {LOG_FILE}")
    print("   Click 'Generate' in the UI — prompts will appear here.")
    print("   Press Ctrl+C to stop.\n")

    last_size = 0
    try:
        while True:
            try:
                size = os.path.getsize(LOG_FILE)
            except OSError:
                size = 0

            if size > last_size:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    f.seek(last_size)
                    new_text = f.read()
                sys.stdout.write(new_text)
                sys.stdout.flush()
                last_size = size

            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n\nStopped.")

if __name__ == "__main__":
    main()
