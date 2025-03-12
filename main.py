import os
import subprocess
import uuid

# Константа с базовой ссылкой на GitHub
GITHUB_RAW_URL = "https://raw.githubusercontent.com/juliakriv0137/video-frames/refs/heads/main/"

def extract_frames(video_path, output_folder, frame_rate):
    """Извлекает кадры из видео с указанной частотой"""
    os.makedirs(output_folder, exist_ok=True)
    
    command = [
        "ffmpeg", "-i", video_path, "-vf",
        f"fps=1/{frame_rate}", f"{output_folder}/frame_%04d.png"
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def count_frames(output_folder):
    """Считает количество извлеченных кадров"""
    return len([f for f in os.listdir(output_folder) if f.endswith(".png")])

def generate_github_links(output_folder):
    """Формирует ссылки на GitHub для кадров"""
    frame_links = []
    folder_name = os.path.basename(output_folder)  # Получаем название папки (UUID)
    
    for i, frame in enumerate(sorted(os.listdir(output_folder)), start=1):
        if frame.endswith(".png"):
            frame_name = f"frame_{i:04d}.png"  # Генерируем корректное имя файла
            frame_path = f"{folder_name}/{frame_name}"
            frame_links.append(f"{GITHUB_RAW_URL}{frame_path}")

    return frame_links

def main():
    video_url = input("Введите ссылку на пост Instagram или YouTube: ")
    frame_rate = input("Введите частоту кадров (в секундах): ")

    try:
        frame_rate = float(frame_rate)
    except ValueError:
        print("Ошибка: частота кадров должна быть числом.")
        return

    # Уникальная папка для каждого видео
    unique_id = str(uuid.uuid4())  # Генерация уникального идентификатора
    output_folder = f"frames/{unique_id}"

    # Скачивание видео
    print("Скачивание видео...")
    video_path = f"videos/{unique_id}/downloaded_video.mp4"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    download_command = ["yt-dlp", "-o", video_path, video_url]
    result = subprocess.run(download_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print("Ошибка при скачивании видео.")
        return

    # Извлечение кадров
    print("Извлечение кадров...")
    extract_frames(video_path, output_folder, frame_rate)

    # Подсчет количества кадров
    frame_count = count_frames(output_folder)
    print(f"✅ Извлечено {frame_count} кадров.")

    # Подтверждение перед отправкой
    input("⏎ Нажмите Enter, чтобы сгенерировать ссылки на кадры...")

    # Генерация ссылок
    frame_links = generate_github_links(output_folder)

    print("\n🔗 **Ссылки на кадры:**")
    for link in frame_links:
        print(link)

if __name__ == "__main__":
    main()
