import subprocess
import time

# run the following command in another terminal window, then run this script
# mlx_audio.server --host 0.0.0.0 --port 9009

SERVER_URL = "http://localhost:9009/v1/audio/speech"
MODEL = "mlx-community/Kokoro-82M-bf16"
INPUT_FILE = "spellingwords.txt"
DELAY = 7  # seconds


def normalize(word: str) -> str:
    return word.strip().replace("’", "").replace("'", "")


def speak_word(word: str):
    print(f"[SAY] {word}")

    # Send request to TTS server using curl → stream to ffplay
    curl = subprocess.Popen(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            SERVER_URL,
            "-H",
            "Content-Type: application/json",
            "-d",
            f'{{"model":"{MODEL}","input":"{word}"}}',
        ],
        stdout=subprocess.PIPE,
    )

    ffplay = subprocess.Popen(
        [
            "ffplay",
            "-autoexit",
            "-nodisp",
            "-loglevel",
            "quiet",
            "-",
        ],
        stdin=curl.stdout,
    )

    ffplay.wait()
    curl.wait()


def main():
    # Load spelling words
    with open(INPUT_FILE, "r") as f:
        words = [normalize(w) for w in f if w.strip()]

    # Speak each word
    for word in words:
        speak_word(word)
        time.sleep(DELAY)


if __name__ == "__main__":
    main()
