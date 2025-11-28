import io
import subprocess
import time
import wave

import requests
import sounddevice as sd
import numpy as np

# Uses mlx-audio HTTP transcription instead of mlx_whisper
SERVER_URL = "http://localhost:9009/v1/audio/speech"
TRANSCRIBE_URL = "http://localhost:9009/v1/audio/transcriptions"
MODEL = "mlx-community/Kokoro-82M-bf16"
STT_MODEL = "mlx-community/whisper-tiny"
INPUT_FILE = "spellingwords.txt"
DELAY = 2  # seconds between interactions
LISTEN_DURATION = 5  # seconds
SAMPLE_RATE = 16000
CURL_CONNECT_TIMEOUT = "5"  # seconds
CURL_MAX_TIME = "60"  # seconds
MAX_SPELL_ATTEMPTS = 2


def normalize(word: str) -> str:
    clean = word.strip().lower()
    for char in [" ", "-", ".", "’", "'", ",", "!", "?"]:
        clean = clean.replace(char, "")
    return clean


def speak_word(word: str, speed: float = 1.0):
    print(f"[SAY] {word} (speed: {speed})")
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
            f'{{"model":"{MODEL}","input":"{word}","speed":{speed}}}',
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


def play_beep(sample_rate: int = SAMPLE_RATE):
    frequency = 1000  # Hz
    beep_duration = 0.2  # seconds
    t = np.linspace(0, beep_duration, int(sample_rate * beep_duration), False)
    beep = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    sd.play(beep, samplerate=sample_rate)
    sd.wait()


def record_audio(duration: int = LISTEN_DURATION, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    print(f"[LISTEN] BEEP! Recording for {duration} seconds...")
    play_beep(sample_rate)

    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return audio_data.squeeze()


def transcribe_audio(audio_data: np.ndarray) -> str:
    print("[THINK] Transcribing...")
    audio_int16 = np.clip(audio_data, -1.0, 1.0)
    audio_int16 = (audio_int16 * np.iinfo(np.int16).max).astype(np.int16)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_int16.tobytes())
    wav_buffer.seek(0)

    response = requests.post(
        TRANSCRIBE_URL,
        data={"model": STT_MODEL},
        files={"file": ("audio.wav", wav_buffer, "audio/wav")},
        timeout=(float(CURL_CONNECT_TIMEOUT), float(CURL_MAX_TIME)),
    )
    response.raise_for_status()
    result = response.json()

    text = result.get("text", "").strip()
    print(f"[HEARD] {text or '[no text returned]'}")
    return text


def main():
    with open(INPUT_FILE, "r") as f:
        words = [w.strip() for w in f if w.strip()]

    for word in words:
        normalized_target = normalize(word)
        attempts = 0
        correct = False
        duration = max(5, len(normalized_target) * 1.2)

        while attempts < MAX_SPELL_ATTEMPTS and not correct:
            speak_word(word)
            audio = record_audio(duration=duration)
            heard_text = transcribe_audio(audio)
            normalized_heard = normalize(heard_text)

            print(f"[DEBUG] Target: '{normalized_target}' | Heard (norm): '{normalized_heard}'")

            if normalized_heard == normalized_target:
                speak_word("Correct!")
                correct = True
            else:
                attempts += 1
                if attempts < MAX_SPELL_ATTEMPTS:
                    speak_word("Not quite. Try again.")
                else:
                    speak_word(f"The word was {word}.")
                    time.sleep(0.5)
                    speak_word("-".join(word).upper(), speed=0.5)

        time.sleep(DELAY)


if __name__ == "__main__":
    main()
