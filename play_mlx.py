import subprocess
import time

# run the following command in another terminal window, then run this script
# mlx_audio.server --host 0.0.0.0 --port 9009

SERVER_URL = "http://localhost:9009/v1/audio/speech"
MODEL = "mlx-community/Kokoro-82M-bf16"
INPUT_FILE = "spellingwords.txt"
DELAY = 7  # seconds
CURL_CONNECT_TIMEOUT = "5"  # seconds
CURL_MAX_TIME = "60"  # seconds


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
            "--connect-timeout",
            CURL_CONNECT_TIMEOUT,
            "--max-time",
            CURL_MAX_TIME,
            "-H",
            "Content-Type: application/json",
            "-d",
            f'{{"model":"{MODEL}","input":"{word}"}}',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
        stderr=subprocess.PIPE,
    )

    ffplay_rc = ffplay.wait()
    curl_rc = curl.wait()

    curl_err = curl.stderr.read().decode("utf-8", "replace").strip() if curl.stderr else ""
    ffplay_err = ffplay.stderr.read().decode("utf-8", "replace").strip() if ffplay.stderr else ""

    if curl_rc != 0:
        raise RuntimeError(f"curl failed with code {curl_rc}: {curl_err or 'no error output'}")
    if ffplay_rc != 0:
        raise RuntimeError(f"ffplay failed with code {ffplay_rc}: {ffplay_err or 'no error output'}")


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
