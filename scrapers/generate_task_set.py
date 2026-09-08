import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from bs4 import BeautifulSoup

# Конфигурация
TASKS_FILE = "data_json/raw/tasks.json"
KES_FILE = "data_json/raw/kes_classifier.json"
STUDENT_SETS_FILE = "data_json/raw/student_sets.json"
PREVIEW_ROOT_DIR = "preview_set"

def generate_task_set():
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        with open(KES_FILE, 'r', encoding='utf-8') as f:
            kes_list = json.load(f)
    except Exception as e:
        print(f"Ошибка при чтении JSON: {e}")
        return

    # Загрузка существующих наборов задач
    student_sets = []
    if os.path.exists(STUDENT_SETS_FILE):
        try:
            with open(STUDENT_SETS_FILE, 'r', encoding='utf-8') as f:
                student_sets = json.load(f)
        except Exception as e:
            print(f"Предупреждение при чтении {STUDENT_SETS_FILE}: {e}")

    # Очистка корневой папки preview_set перед началом работы
    if os.path.exists(PREVIEW_ROOT_DIR):
        shutil.rmtree(PREVIEW_ROOT_DIR)
    os.makedirs(PREVIEW_ROOT_DIR, exist_ok=True)

    # Создаем карту KES для быстрого поиска: {uuid: {number, title}}
    kes_map = {k['uuid']: k for k in kes_list}

    # Параметры генерации вариантов
    target_numbers = [2, 4]
    num_variants = 2

    # Группируем все доступные задачи по номерам ЕГЭ
    tasks_by_num = {num: [t for t in tasks if t.get('ege_number') == num] for num in target_numbers}

    for variant_idx in range(1, num_variants + 1):
        variant_dir = os.path.join(PREVIEW_ROOT_DIR, str(variant_idx))
        variant_images_dir = os.path.join(variant_dir, "images")
        variant_files_dir = os.path.join(variant_dir, "files")
        variant_output_file = os.path.join(variant_dir, "index.html")

        os.makedirs(variant_images_dir, exist_ok=True)
        os.makedirs(variant_files_dir, exist_ok=True)

        # Отбираем по одной задаче для каждого номера с отступом 10
        selected_tasks = []
        for num in target_numbers:
            filtered = tasks_by_num[num]
            if filtered:
                idx = 10 + (variant_idx - 1)
                if idx < len(filtered):
                    selected_tasks.append((num, filtered[idx]))
                else:
                    selected_tasks.append((num, filtered[-1]))
            else:
                print(f"Вариант {variant_idx}: Задания с номером {num} не найдены.")

        # Создаем запись о наборе задач (Student Set)
        set_uuid = str(uuid.uuid4())
        set_name = f"Задания ЕГЭ по информатике 2026: Вариант {variant_idx}"

        # Формируем список связей с задачами (для соответствия student_set_tasks)
        task_links = []
        for i, (num, task) in enumerate(selected_tasks, 1):
            task_links.append({
                "task_uuid": task['uuid'],
                "task_order": i
            })

        set_data = {
            "uuid": set_uuid,
            "name": set_name,
            "student_uuid": None, # Наборы создаются без привязки к студенту
            "date_created": datetime.now().isoformat(),
            "tasks": task_links
        }
        student_sets.append(set_data)

        html_start = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>{set_name}</title>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
                .task-container {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    border: 1px solid #ddd;
                }}
                .task-header {{
                    border-bottom: 2px solid #eee;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    display: flex;
                    justify-content: space-between;
                    font-weight: bold;
                    color: #555;
                }}
                .kes-list {{
                    font-size: 0.9em;
                    color: #666;
                    margin-bottom: 15px;
                    font-style: italic;
                    line-height: 1.4;
                }}
                .kes-item {{
                    display: block;
                    margin-bottom: 2px;
                }}
                .task-body {{
                    line-height: 1.6;
                    margin-bottom: 15px;
                }}
                .task-body img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 10px 0;
                    border: 1px solid #eee;
                }}
                .task-files {{
                    background: #f9f9f9;
                    padding: 10px;
                    border-radius: 4px;
                    border: 1px solid #eee;
                    margin-bottom: 15px;
                    font-size: 0.9em;
                }}
                .task-files strong {{
                    display: block;
                    margin-bottom: 5px;
                    color: #444;
                }}
                .task-files ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .task-files li {{
                    margin-bottom: 3px;
                }}
                .footer {{
                    margin-top: 10px;
                    font-size: 0.8em;
                    color: #999;
                    text-align: right;
                }}
                .debug-info {{
                    background: #fff3cd;
                    padding: 5px;
                    font-size: 0.8em;
                    border: 1px solid #ffeeba;
                    margin-bottom: 10px;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <h1>{set_name}</h1>
            <p>Задания: 2, 4, 7, 13</p>
        """

        html_end = "</body></html>"
        full_html = html_start

        for ege_num, task in selected_tasks:
            # 1. Формируем список КЭС
            kes_html_items = []
            for uid in task['kes_uuids']:
                section = kes_map.get(uid)
                if section:
                    num = section.get('kes_number', '').strip()
                    title = section.get('title', '').strip()
                    display_num = num if num else "•"
                    kes_html_items.append(f'<span class="kes-item">{display_num} {title}</span>')

            kes_text_html = "".join(kes_html_items) if kes_html_items else "Не указано"

            soup = BeautifulSoup(task['html_content'], 'html.parser')

            # 2. Копируем и исправляем пути для <img>
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    if not src.startswith('http') and not src.startswith('/'):
                        source_path = os.path.join("data_json/images", src)
                        dest_path = os.path.join(variant_images_dir, src)
                        if os.path.exists(source_path):
                            shutil.copy2(source_path, dest_path)
                            img['src'] = f"images/{src}"
                        else:
                            img['style'] = 'opacity: 0.3; border: 1px solid red;'
                            img['title'] = f'Файл не найден: {source_path}'
                    else:
                        img['style'] = 'opacity: 0.3; filter: grayscale(1);'
                        img['title'] = 'Внешняя ссылка (не скопирована)'

            # 3. Обрабатываем ссылки на файлы внутри HTML
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.startswith('files/'):
                    source_path = os.path.join("data_json", href)
                    dest_path = os.path.join(variant_dir, href)
                    if os.path.exists(source_path):
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                        a['href'] = href
                    else:
                        a['style'] = 'color: red; text-decoration: line-through;'
                        a['title'] = f'Файл не найден: {source_path}'

            task_html = str(soup)

            # 4. Создаем отдельный блок ссылок на файлы под заданием
            files_html = ""
            task_files_dir = os.path.join("data_json/files", task['uuid'])
            if os.path.exists(task_files_dir):
                files = sorted(os.listdir(task_files_dir))
                if files:
                    files_html = '<div class="task-files"><strong>Прикрепленные файлы:</strong><ul>'
                    for f in files:
                        rel_path = f"files/{task['uuid']}/{f}"
                        source_path = os.path.join("data_json", rel_path)
                        dest_path = os.path.join(variant_dir, rel_path)

                        if os.path.exists(source_path):
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            shutil.copy2(source_path, dest_path)
                            files_html += f'<li><a href="{rel_path}" target="_blank">{f}</a></li>'
                    files_html += '</ul></div>'

            full_html += f"""
            <div class="task-container">
                <div class="task-header">
                    <span>Номер задания: {ege_num} | ID: {task['original_id']}</span>
                    <span>Тип ответа: {task['answer_type']}</span>
                </div>
                <div class="kes-list">КЭС:<br>{kes_text_html}</div>
                <div class="debug-info">
                    Картинок: {task['image_count']} | Файлов: {task['file_count']}
                </div>
                <div class="task-body">
                    {task_html}
                </div>
                {files_html}
                <div class="footer">UUID: {task['uuid']}</div>
            </div>
            """

        full_html += html_end

        with open(variant_output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)

        # Создание ZIP-архива папки варианта
        zip_filename = os.path.join(PREVIEW_ROOT_DIR, f"Вариант {variant_idx}.zip")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(variant_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(variant_dir))
                    zipf.write(file_path, arcname)

        print(f"Вариант {variant_idx} создан в: {variant_dir} и заархивирован в {zip_filename}")

    # Сохранение наборов задач в JSON
    with open(STUDENT_SETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(student_sets, f, ensure_ascii=False, indent=4)

    print(f"Данные о наборах задач сохранены в: {STUDENT_SETS_FILE}")

if __name__ == "__main__":
    generate_task_set()
