import requests
import time
import subprocess
import uuid
import shutil
from pathlib import Path
import logging
import yt_dlp  # Для скачивания видео
from dotenv import load_dotenv
import os
import git  # Для работы с GitHub

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("\u274c Ошибка: API-ключ OpenAI не найден! Проверьте .env файл.")

# GitHub данные
GITHUB_REPO = "https://github.com/juliakriv0137/video-frames.git"
GITHUB_LOCAL_PATH = Path("video-frames")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")


def download_video(url: str, output_dir: Path) -> Path:
    """Скачивает видео с Instagram через yt-dlp."""
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "downloaded_video.mp4"

    ydl_opts = {
        "outtmpl": str(video_path),
        "format": "best",
        "quiet": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return video_path
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео: {e}")
        raise


def extract_frames(video_path: Path, frames_dir: Path, fps: float):
    """Извлекает кадры из видео."""
    try:
        frames_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-i", str(video_path), "-vf", f"fps=1/{fps}", f"{frames_dir}/frame_%04d.png"
        ], check=True)
        video_path.unlink()
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при извлечении кадров: {e}")
        raise


def upload_frames_to_github(frames_dir: Path):
    """Загружает кадры на GitHub."""
    if not GITHUB_LOCAL_PATH.exists():
        git.Repo.clone_from(GITHUB_REPO, GITHUB_LOCAL_PATH)
    
    repo = git.Repo(GITHUB_LOCAL_PATH)
    
    # Копируем кадры в локальный репозиторий
    destination = GITHUB_LOCAL_PATH / frames_dir.name
    shutil.copytree(frames_dir, destination, dirs_exist_ok=True)

    repo.git.add(A=True)
    repo.index.commit(f"Добавлены кадры {frames_dir.name}")
    origin = repo.remote(name='origin')
    origin.push()

    return f"https://github.com/juliakriv0137/video-frames/tree/main/{frames_dir.name}"


def analyze_image(image_url: str) -> str:
    """Анализирует изображение с помощью OpenAI API."""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Детально опиши, что происходит на изображении."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}}
            ]}
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        logger.error(f"Ошибка при анализе изображения: {e}")
        return "Ошибка анализа изображения."


def analyze_video(url: str, fps: float):
    """Обрабатывает видео, загружает кадры в GitHub и передает их GPT."""
    task_id = str(uuid.uuid4())
    frames_dir = Path("frames") / task_id
    
    try:
        video_path = download_video(url, Path("videos") / task_id)
        extract_frames(video_path, frames_dir, fps)
        github_link = upload_frames_to_github(frames_dir)

        summary_payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "Проанализируй кадры и составь описание видео."},
                {"role": "user", "content": f"Вот ссылка на кадры: {github_link}"
                }
            ],
            "max_tokens": 1200
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}, json=summary_payload)
        response.raise_for_status()
        video_summary = response.json()["choices"][0]["message"]["content"]
        
        return {"summary": video_summary, "frames_url": github_link}
    except Exception as e:
        logger.error(f"Ошибка в процессе анализа видео: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    video_url = input("Введите ссылку на пост Instagram или YouTube: ")
    fps = float(input("Введите частоту кадров (в секундах): "))
    result = analyze_video(video_url, fps)
    print("\nРезультаты анализа:")
    print(result)