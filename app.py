import os
import json
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone

load_dotenv()
app = Flask(__name__)
TOGGL_API_TOKEN = os.getenv('TOGGL_API_TOKEN')
WORKSPACE_ID = None

def ms_to_hms(ms):
    """Конвертирует миллисекунды в строку HH:MM:SS."""
    if ms is None: ms = 0
    seconds = int(ms / 1000)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def initialize_app_data():
    """Получает Workspace ID при старте."""
    global WORKSPACE_ID
    if not TOGGL_API_TOKEN:
        raise ValueError("Не найден TOGGL_API_TOKEN в .env файле!")
    try:
        url = "https://api.track.toggl.com/api/v9/me/workspaces"
        response = requests.get(url, auth=(TOGGL_API_TOKEN, "api_token"))
        response.raise_for_status()
        workspaces = response.json()
        if not workspaces:
            raise ValueError("Не найдено ни одного рабочего пространства (workspace).")
        WORKSPACE_ID = workspaces[0]['id']
        print(f"Успешно определен Workspace ID: {WORKSPACE_ID}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Ошибка при запросе к Toggl API: {e}")

def get_projects(workspace_id):
    """Получает список всех активных проектов в Workspace."""
    url = f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects?active=true"
    response = requests.get(url, auth=(TOGGL_API_TOKEN, "api_token"))
    return response.json() or []

def get_daily_summary(workspace_id):
    """Получает сводный отчет за сегодня. Финальная рабочая версия."""
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    url = f"https://api.track.toggl.com/reports/api/v3/workspace/{workspace_id}/summary/time_entries"
    payload = {
        "start_date": today_str,
        "end_date": today_str,
        "grouping": "projects",
        "subgrouping": "time_entries"
    }
    
    try:
        response = requests.post(url, auth=(TOGGL_API_TOKEN, "api_token"), json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Reports API: {e}")
        return {"total_today": "Ошибка", "projects": {}}
    
    data = response.json()
    total_today_ms = 0
    project_summary = {}
    
    for group in data.get('groups', []):
        project_id = group.get('id')
        project_time_ms = sum(subgroup.get('seconds', 0) * 1000 for subgroup in group.get('sub_groups', []))
        total_today_ms += project_time_ms
        if project_id is not None:
             project_summary[project_id] = ms_to_hms(project_time_ms)

    return {
        "total_today": ms_to_hms(total_today_ms),
        "projects": project_summary
    }

def get_toggl_status():
    url = "https://api.track.toggl.com/api/v9/me/time_entries/current"
    try:
        response = requests.get(url, auth=(TOGGL_API_TOKEN, "api_token"), timeout=5)
        response.raise_for_status()
        current_timer = response.json()
        if not current_timer: return {"status": "stopped", "text": "Таймер остановлен"}
        
        description = current_timer.get('description', 'Без описания')
        start_time_str = current_timer.get('start')
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        duration = datetime.now(timezone.utc) - start_time
        
        return {
            "status": "running",
            "text": description,
            "duration": ms_to_hms(duration.total_seconds() * 1000),
            "id": current_timer.get('id'),
            "project_id": current_timer.get('project_id'),
            "start": start_time_str
        }
    except requests.exceptions.RequestException: return {"status": "error", "text": "Ошибка API"}

def start_toggl_timer(description, project_id):
    url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/time_entries"
    payload = { "description": description, "start": datetime.now(timezone.utc).isoformat(), "duration": -1, "workspace_id": WORKSPACE_ID, "project_id": project_id, "created_with": "Toggl Webapp" }
    requests.post(url, auth=(TOGGL_API_TOKEN, "api_token"), json=payload)
    return {"result": "ok"}

def stop_toggl_timer(timer_id):
    if timer_id:
        url = f"https://api.track.toggl.com/api/v9/workspaces/{WORKSPACE_ID}/time_entries/{timer_id}/stop"
        requests.patch(url, auth=(TOGGL_API_TOKEN, "api_token"))
    return {"result": "ok"}

@app.route('/')
def index():
    projects = get_projects(WORKSPACE_ID)
    return render_template('index.html', projects=projects)

@app.route('/api/status')
def api_status():
    return jsonify(get_toggl_status())

@app.route('/api/summary')
def api_summary():
    return jsonify(get_daily_summary(WORKSPACE_ID))

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    status = get_toggl_status()
    if status.get('status') == 'running':
        stop_toggl_timer(status.get('id'))
    else:
        data = request.get_json()
        start_toggl_timer(data.get('description'), data.get('projectId'))
    return jsonify({"result": "toggled"})

if __name__ == '__main__':
    try:
        initialize_app_data()
    except ValueError as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")
        exit(1)