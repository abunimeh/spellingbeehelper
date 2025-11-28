# Spelling Bee Helper

This program helps students practicing their spelling bee words. It uses MLX to generate Text to Speech using `mlx-community/Kokoro-82M-bf16`

## Setup

This project uses `pixi` for dependency management. To set up the project, ensure you have [`pixi`](https://pixi.sh) installed. Then, run the following command in the project root:

Clone this repo to your favorite directory:

```bash
cd FAV_DIRECTORY
```

Install all dependencies:
```bash
pixi install
```

## How to Run

To run the main application, open _TWO_ terminal windows:


In the 1st window run the server:
```bash
pixi run server
```

In the 2nd window, run the audio player:
```bash
pixi run audio
```

If you want to the student to have a test with AI, run:
```bash
pixi run test
```

## NOTES

Note that the 1st time you launch the audio player, it will download the model from huggingface. After that run, it will be cached and run quickly.

If you want to increase the delay between words, edit play_mlx.py `DELAY` variable.