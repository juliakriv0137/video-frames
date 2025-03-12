import os
import subprocess
import uuid
import re
import json

def download_video(video_url, output_folder):
    """Скачивает видео по ссылке и возвращает его путь."""
    os.makedirs(output_folder, exist_ok=True)
    video_id = str(uuid.uuid4())  
    video_path = f"{output_folder}/{video_id}/downloaded_video.mp4"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    command = [
        "yt-dlp",
        "-o", video_path,
        "-f", "mp4",
        video_url
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Видео скачано: {video_path}")
        return video_id, video_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при скачивании видео:\n{e.stderr}")
        return None, None

def extract_frames(video_path, output_folder, frame_rate):
    """Извлекает кадры из видео и возвращает их количество."""
    if not os.path.exists(video_path):
        print("❌ Ошибка: Видео не найдено!")
        return 0

    os.makedirs(output_folder, exist_ok=True)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps=1/{frame_rate}",
        f"{output_folder}/frame_%04d.png"
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Подсчёт количества кадров
        frame_files = sorted(
            [f for f in os.listdir(output_folder) if re.match(r'frame_\d+\.png', f)]
        )
        frame_count = len(frame_files)

        if frame_count == 0:
            print("⚠️ Кадры не были извлечены!")
            return 0

        print(f"📸 Извлечено {frame_count} кадров")
        return frame_count
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при извлечении кадров:\n{e.stderr}")
        return 0

def generate_github_links(folder_name, frame_count):
    """Создаёт ссылки на каждый кадр в GitHub."""
    base_url = "https://github.com/juliakriv0137/video-frames/blob/main"

    frame_links = [
        f"{base_url}/{folder_name}/frame_{i:04d}.png?raw=true"
        for i in range(1, frame_count + 1)
    ]

    return frame_links

def get_validated_input(prompt, expected_type):
    """Функция для безопасного ввода данных."""
    while True:
        user_input = input(prompt).strip()
        
        if expected_type == "url":
            if user_input.startswith("http"):
                return user_input
            else:
                print("❌ Ошибка: Введите корректную ссылку на видео!")

        elif expected_type == "int":
            try:
                value = int(user_input)
                if value > 0:
                    return value
                else:
                    print("❌ Ошибка: Введите положительное число!")
            except ValueError:
                print("❌ Ошибка: Введите корректное число!")

def main():
    # Получаем корректные данные
    video_url = get_validated_input("Введите ссылку на пост Instagram или YouTube: ", "url")
    frame_rate = get_validated_input("Введите частоту кадров (в секундах): ", "int")

    output_folder = "videos"
    frame_folder = "frames"

    # 1. Скачиваем видео
    video_id, video_path = download_video(video_url, output_folder)
    if not video_id:
        print("❌ Не удалось скачать видео.")
        return

    # 2. Извлекаем кадры
    frame_output_folder = f"{frame_folder}/{video_id}"
    frame_count = extract_frames(video_path, frame_output_folder, frame_rate)

    if frame_count == 0:
        print("❌ Не удалось извлечь кадры.")
        return

    # 3. Генерируем ссылки на кадры
    frame_links = generate_github_links(video_id, frame_count)

    # 4. Вывод ссылок для проверки
    print("\n🔗 Ссылки на кадры (первые 5):")
    for link in frame_links[:5]:  # Покажем первые 5 ссылок для проверки
        print(link)

    input("\n✅ Проверь ссылки выше. Если всё верно, нажми Enter для отправки GPT...")

    # 5. Отправляем GPT только после подтверждения
    result = {
        "summary": f"✅ Видео обработано. Извлечено {frame_count} кадров.",
        "frames_urls": frame_links
    }

    print(json.dumps(result, indent=4, ensure_ascii=False))  # ensure_ascii=False для корректного отображения

if __name__ == "__main__":
    main()
