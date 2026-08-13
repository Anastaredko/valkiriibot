import telebot
import json
import os
from datetime import datetime, timedelta

# ==================== КОНФИГ ====================
SPHERES = [
    {"name": "Здоровье", "emoji": "🏥"},
    {"name": "Карьера", "emoji": "💼"},
    {"name": "Финансы", "emoji": "💰"},
    {"name": "Отношения", "emoji": "💕"},
    {"name": "Семья", "emoji": "👨‍👩‍👧‍👦"},
    {"name": "Хобби", "emoji": "🎨"},
    {"name": "Саморазвитие", "emoji": "📚"}
]

TASKS_PER_SPHERE = 2
MAX_TASKS_PER_USER = len(SPHERES) * TASKS_PER_SPHERE
SPRINT_START = datetime(2026, 8, 17, 10, 0, 0)

# ==================== МОДЕЛИ ====================
class Complexity:
    EASY = "легкая"
    MEDIUM = "средняя"
    HARD = "сложная"
    POINTS = {EASY: 1, MEDIUM: 2, HARD: 3}

class TaskStatus:
    NOT_STARTED = "не начата"
    STARTED = "начата"
    IN_PROGRESS = "в процессе"
    ALMOST_DONE = "почти готова"
    COMPLETED = "выполнена"
    FAILED = "провалена"
    PROGRESS = {NOT_STARTED: 0, STARTED: 25, IN_PROGRESS: 50, ALMOST_DONE: 75, COMPLETED: 100, FAILED: 0}
    USER_STATUSES = [NOT_STARTED, STARTED, IN_PROGRESS, ALMOST_DONE, COMPLETED]

class SprintStatus:
    WAITING = "waiting"
    ACTIVE = "active"
    VOTING = "voting"
    FINISHED = "finished"

# ==================== ХРАНИЛИЩЕ ====================
class Storage:
    def __init__(self, file_path="data.json"):
        self.file_path = file_path
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"users": {}, "sprints": [], "tasks": [], "votes": [], "task_counter": 0, "vote_counter": 0, "sprint_counter": 0}
    
    def _save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id):
        data = self.data["users"].get(str(user_id))
        if data:
            return data
        return None
    
    def get_all_users(self):
        return list(self.data["users"].values())
    
    def create_user(self, user_id, username, full_name):
        if str(user_id) not in self.data["users"]:
            user = {
                "id": user_id,
                "username": username or str(user_id),
                "full_name": full_name,
                "registered_at": datetime.now().isoformat()
            }
            self.data["users"][str(user_id)] = user
            self._save()
        return self.get_user(user_id)
    
    def get_active_sprint(self):
        for data in self.data["sprints"]:
            if data["status"] == SprintStatus.ACTIVE:
                return data
        return None
    
    def get_waiting_sprint(self):
        for data in self.data["sprints"]:
            if data["status"] == SprintStatus.WAITING:
                return data
        return None
    
    def get_voting_sprint(self):
        for data in self.data["sprints"]:
            if data["status"] == SprintStatus.VOTING:
                return data
        return None
    
    def get_current_sprint(self):
        for data in reversed(self.data["sprints"]):
            if data["status"] in [SprintStatus.WAITING, SprintStatus.ACTIVE, SprintStatus.VOTING]:
                return data
        return None
    
    def get_last_finished_sprint(self):
        for data in reversed(self.data["sprints"]):
            if data["status"] == SprintStatus.FINISHED:
                return data
        return None
    
    def create_sprint(self, start_date):
        self.data["sprint_counter"] += 1
        now = datetime.now()
        end_date = start_date + timedelta(days=14)
        sprint = {
            "id": int(now.timestamp()),
            "number": self.data["sprint_counter"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": SprintStatus.WAITING,
            "voting_end_date": None,
            "winner_id": None
        }
        self.data["sprints"].append(sprint)
        self._save()
        return sprint
    
    def update_sprint_status(self, sprint_id, status):
        for data in self.data["sprints"]:
            if data["id"] == sprint_id:
                data["status"] = status
                if status == SprintStatus.VOTING:
                    data["voting_end_date"] = (datetime.now() + timedelta(hours=24)).isoformat()
                self._save()
                return True
        return False
    
    def set_sprint_winner(self, sprint_id, winner_id):
        for data in self.data["sprints"]:
            if data["id"] == sprint_id:
                data["winner_id"] = winner_id
                data["status"] = SprintStatus.FINISHED
                self._save()
                return True
        return False
    
    def create_task(self, user_id, sprint_id, sphere, description, complexity, is_draft=False):
        self.data["task_counter"] += 1
        now = datetime.now().isoformat()
        task = {
            "id": self.data["task_counter"],
            "user_id": user_id,
            "sprint_id": sprint_id,
            "sphere": sphere,
            "description": description,
            "complexity": complexity,
            "status": TaskStatus.NOT_STARTED,
            "is_draft": is_draft,
            "created_at": now,
            "updated_at": now
        }
        self.data["tasks"].append(task)
        self._save()
        return task
    
    def get_task(self, task_id):
        for data in self.data["tasks"]:
            if data["id"] == task_id:
                return data
        return None
    
    def get_user_tasks(self, user_id, sprint_id):
        return [t for t in self.data["tasks"] if t["user_id"] == user_id and t["sprint_id"] == sprint_id]
    
    def get_user_tasks_by_sphere(self, user_id, sprint_id, sphere):
        return [t for t in self.data["tasks"] if t["user_id"] == user_id and t["sprint_id"] == sprint_id and t["sphere"] == sphere]
    
    def get_sprint_tasks(self, sprint_id):
        return [t for t in self.data["tasks"] if t["sprint_id"] == sprint_id]
    
    def update_task_status(self, task_id, status):
        for data in self.data["tasks"]:
            if data["id"] == task_id:
                data["status"] = status
                data["updated_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def delete_task(self, task_id):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        self._save()
    
    def get_user_task_count(self, user_id, sprint_id):
        return len(self.get_user_tasks(user_id, sprint_id))
    
    def get_user_task_count_by_sphere(self, user_id, sprint_id, sphere):
        return len(self.get_user_tasks_by_sphere(user_id, sprint_id, sphere))
    
    def create_vote(self, sprint_id, voter_id, candidate_id):
        self.data["vote_counter"] += 1
        vote = {
            "id": self.data["vote_counter"],
            "sprint_id": sprint_id,
            "voter_id": voter_id,
            "candidate_id": candidate_id,
            "created_at": datetime.now().isoformat()
        }
        self.data["votes"].append(vote)
        self._save()
        return vote
    
    def get_user_vote(self, sprint_id, voter_id):
        for data in self.data["votes"]:
            if data["sprint_id"] == sprint_id and data["voter_id"] == voter_id:
                return data
        return None
    
    def get_all_votes(self, sprint_id):
        return [v for v in self.data["votes"] if v["sprint_id"] == sprint_id]
    
    def get_sprint_results(self, sprint_id):
        tasks = self.get_sprint_tasks(sprint_id)
        votes = self.get_all_votes(sprint_id)
        users = self.get_all_users()
        
        user_tasks = {}
        for task in tasks:
            if task["user_id"] not in user_tasks:
                user_tasks[task["user_id"]] = []
            user_tasks[task["user_id"]].append(task)
        
        vote_counts = {}
        for vote in votes:
            vote_counts[vote["candidate_id"]] = vote_counts.get(vote["candidate_id"], 0) + 1
        
        results = []
        for user in users:
            if user["id"] in user_tasks:
                tasks_list = user_tasks[user["id"]]
                task_points = 0
                for t in tasks_list:
                    progress = TaskStatus.PROGRESS.get(t["status"], 0)
                    max_points = Complexity.POINTS.get(t["complexity"], 1)
                    task_points += max_points * (progress / 100)
                vote_count = vote_counts.get(user["id"], 0)
                results.append({
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "tasks": tasks_list,
                    "task_points": round(task_points, 1),
                    "vote_count": vote_count,
                    "total_points": round(task_points + vote_count, 1),
                    "is_winner": False
                })
        
        results.sort(key=lambda x: x["total_points"], reverse=True)
        if results:
            results[0]["is_winner"] = True
        return results

# ==================== БОТ ====================
storage = Storage()

waiting_sprint = storage.get_waiting_sprint()
if not waiting_sprint:
    storage.create_sprint(SPRINT_START)

bot = telebot.TeleBot("8063432147:AAEZCNkjYy5mj9BKX4qwPNczWtDpQCPrLEA")

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_status_emoji(status):
    emojis = {"не начата": "⏳", "начата": "🔄", "в процессе": "⚡", "почти готова": "📈", "выполнена": "✅", "провалена": "❌"}
    return emojis.get(status, "⚪")

def get_complexity_emoji(complexity):
    emojis = {"легкая": "🟢", "средняя": "🟡", "сложная": "🔴"}
    return emojis.get(complexity, "⚪")

def format_task_card(task):
    status_emoji = get_status_emoji(task["status"])
    complexity_emoji = get_complexity_emoji(task["complexity"])
    progress = TaskStatus.PROGRESS.get(task["status"], 0)
    max_points = Complexity.POINTS.get(task["complexity"], 1)
    points = max_points * (progress / 100)
    return f"{status_emoji} <b>{task['description']}</b>\n   {complexity_emoji} Сфера: {task['sphere']}\n   📊 Сложность: {task['complexity'].capitalize()} ({max_points} баллов)\n   📈 Прогресс: {progress}% (Статус: {task['status']})\n   💯 Баллы: {points:.1f} / {max_points}"

def get_time_until_start():
    now = datetime.now()
    if now >= SPRINT_START:
        return "✅ Спринт уже начался!"
    diff = SPRINT_START - now
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    seconds = diff.seconds % 60
    parts = []
    if days > 0:
        parts.append(f"{days} д")
    if hours > 0:
        parts.append(f"{hours} ч")
    if minutes > 0:
        parts.append(f"{minutes} м")
    if seconds > 0:
        parts.append(f"{seconds} с")
    return "⏳ " + " ".join(parts) if parts else "✅ Спринт начался!"

def is_sprint_active():
    return datetime.now() >= SPRINT_START

def get_sphere_progress(user_id, sprint_id, sphere_name):
    tasks = storage.get_user_tasks_by_sphere(user_id, sprint_id, sphere_name)
    if not tasks:
        return 0
    total_progress = sum(TaskStatus.PROGRESS.get(t["status"], 0) for t in tasks)
    return round(total_progress / len(tasks))

def get_user_sphere_progress(user_id, sprint_id):
    progress = {}
    for sphere in SPHERES:
        progress[sphere["name"]] = get_sphere_progress(user_id, sprint_id, sphere["name"])
    return progress

def get_wheel_visual(progress_data):
    lines = []
    for sphere in SPHERES:
        name = sphere["name"]
        emoji = sphere["emoji"]
        progress = progress_data.get(name, 0)
        filled = int(progress / 10)
        empty = 10 - filled
        bar = "▓" * filled + "░" * empty
        lines.append(f"{emoji} {name[:12].ljust(12)}: {bar} {progress}%")
    return "\n".join(lines)

def get_user_sphere_summary(user_id, sprint_id):
    lines = []
    for sphere in SPHERES:
        tasks = storage.get_user_tasks_by_sphere(user_id, sprint_id, sphere["name"])
        completed = len([t for t in tasks if t["status"] == TaskStatus.COMPLETED])
        total = len(tasks)
        progress = get_sphere_progress(user_id, sprint_id, sphere["name"])
        lines.append(f"{sphere['emoji']} {sphere['name']}: {completed}/{total} задач, {progress}%")
    return "\n".join(lines)

# ==================== КЛАВИАТУРЫ ====================
def main_menu():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    if is_sprint_active():
        keyboard.add(
            telebot.types.InlineKeyboardButton("🔄 Колесо баланса", callback_data="wheel"),
            telebot.types.InlineKeyboardButton("📋 Мои задачи", callback_data="my_tasks"),
            telebot.types.InlineKeyboardButton("👥 Задачи команды", callback_data="team_tasks"),
            telebot.types.InlineKeyboardButton("➕ Создать задачу", callback_data="create_task"),
            telebot.types.InlineKeyboardButton("📊 Статус спринта", callback_data="sprint_status")
        )
        voting_sprint = storage.get_voting_sprint()
        if voting_sprint:
            keyboard.add(telebot.types.InlineKeyboardButton("⭐ Проголосовать", callback_data="vote"))
        else:
            finished_sprint = storage.get_last_finished_sprint()
            if finished_sprint:
                keyboard.add(telebot.types.InlineKeyboardButton("🏆 Итоги спринта", callback_data="sprint_results"))
    else:
        keyboard.add(
            telebot.types.InlineKeyboardButton("📝 Поставить задачи", callback_data="create_task"),
            telebot.types.InlineKeyboardButton("👥 Участники спринта", callback_data="team_tasks")
        )
    
    keyboard.add(telebot.types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help"))
    return keyboard

def spheres_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for s in SPHERES:
        keyboard.add(telebot.types.InlineKeyboardButton(f"{s['emoji']} {s['name']}", callback_data=f"sphere_{s['name']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

def complexity_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🟢 Лёгкая (1 балл)", callback_data="complexity_легкая"),
        telebot.types.InlineKeyboardButton("🟡 Средняя (2 балла)", callback_data="complexity_средняя")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("🔴 Сложная (3 балла)", callback_data="complexity_сложная")
    )
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

def task_statuses_keyboard(task_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("⏳ Не начата (0%)", callback_data=f"status_{task_id}_не начата"),
        telebot.types.InlineKeyboardButton("🔄 Начата (25%)", callback_data=f"status_{task_id}_начата")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("⚡ В процессе (50%)", callback_data=f"status_{task_id}_в процессе"),
        telebot.types.InlineKeyboardButton("📈 Почти готова (75%)", callback_data=f"status_{task_id}_почти готова")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("✅ Выполнена (100%)", callback_data=f"status_{task_id}_выполнена")
    )
    keyboard.add(telebot.types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{task_id}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="my_tasks"))
    return keyboard

def back_button():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

def voting_keyboard(candidates, sprint_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for c in candidates:
        keyboard.add(telebot.types.InlineKeyboardButton(f"👤 {c['full_name']}", callback_data=f"vote_{sprint_id}_{c['user_id']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

# ==================== ОБРАБОТЧИКИ ====================
@bot.message_handler(commands=['start'])
def start_message(message):
    user = message.from_user
    storage.create_user(user.id, user.username, user.full_name)
    
    if not is_sprint_active():
        timer_text = get_time_until_start()
        text = (
            f"🌟 Привет, {user.full_name}!\n\n"
            f"Мы на пороге нового рывка 🚀\n"
            f"Спринт стартует: {SPRINT_START.strftime('%d.%m.%Y в %H:%M')}\n"
            f"Осталось: {timer_text}\n\n"
            f"✨ Правила игры:\n"
            f"• Поставь по {TASKS_PER_SPHERE} задачи на каждую из {len(SPHERES)} сфер жизни\n"
            f"• Всего {MAX_TASKS_PER_USER} задач на спринт\n"
            f"• Каждая задача — твой шаг к балансу и росту\n\n"
            f"Пока можно:\n"
            f"📝 Наметить задачи\n"
            f"👥 Ознакомиться с участниками\n\n"
            f"Готовься — скоро начинаем! 💪"
        )
    else:
        active_sprint = storage.get_active_sprint()
        if active_sprint:
            end_date = datetime.fromisoformat(active_sprint['end_date'])
            days_left = max(0, (end_date - datetime.now()).days)
            text = (
                f"🔥 Ты в игре, {user.full_name}!\n\n"
                f"Спринт #{active_sprint['number']} уже здесь 🚀\n"
                f"До финиша: {days_left} дней\n\n"
                f"Напомню, что внутри:\n"
                f"• {len(SPHERES)} сфер, по {TASKS_PER_SPHERE} задачи на каждую = {MAX_TASKS_PER_USER} дел\n"
                f"• Каждый день ты сможешь отслеживать свой прогресс\n"
                f"• Каждый день — маленький, но важный шаг\n\n"
                f"Делай, как чувствуешь.\n"
                f"Ты справишься! 💫"
            )
    
    # Отправляем картинку по ссылке + текст
    try:
        bot.send_photo(
            message.chat.id,
            photo="https://raw.githubusercontent.com/Anastaredko/valkiriibot/main/images/2.png",
            caption=text,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Не удалось отправить картинку: {e}")
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    user_id = call.from_user.id

    if data == "back_to_main":
        bot.edit_message_text("🎯 Главная\nВыбери, что хочешь сделать:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return

    if data == "help":
        help_text = "📖 <b>Помощь по боту</b>\n\n"
        if not is_sprint_active():
            help_text += "⏳ <b>Режим ожидания:</b>\n"
            help_text += "• 📝 Поставить задачи — выбрать задачи на спринт\n"
            help_text += "• 👥 Участники спринта — список участников\n\n"
        else:
            help_text += "🚀 <b>Активный режим:</b>\n"
            help_text += "• 🔄 Колесо баланса — визуализация прогресса\n"
            help_text += "• 📋 Мои задачи — просмотр и управление\n"
            help_text += "• 👥 Задачи команды — просмотр всех задач\n"
            help_text += "• ➕ Создать задачу — добавление новой\n"
            help_text += "• 📊 Статус спринта — общая статистика\n"
            help_text += "• ⭐ Проголосовать — после завершения спринта\n"
            help_text += "• 🏆 Итоги спринта — результаты"
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=back_button(), parse_mode="HTML")
        return

    if data == "wheel":
        if not is_sprint_active():
            bot.answer_callback_query(call.id, "⏳ Спринт ещё не начался!", show_alert=True)
            return
        show_wheel(call)
        return

    if data == "my_tasks":
        if not is_sprint_active():
            bot.answer_callback_query(call.id, "⏳ Спринт ещё не начался!", show_alert=True)
            return
        show_my_tasks(call)
        return

    if data == "team_tasks":
        show_team_members(call)
        return

    if data == "create_task":
        start_create_task(call)
        return

    if data == "sprint_status":
        if not is_sprint_active():
            bot.answer_callback_query(call.id, "⏳ Спринт ещё не начался!", show_alert=True)
            return
        show_sprint_status(call)
        return

    if data == "vote":
        if not is_sprint_active():
            bot.answer_callback_query(call.id, "⏳ Спринт ещё не начался!", show_alert=True)
            return
        start_voting(call)
        return

    if data == "sprint_results":
        if not is_sprint_active():
            bot.answer_callback_query(call.id, "⏳ Спринт ещё не начался!", show_alert=True)
            return
        show_sprint_results(call)
        return

    if data.startswith("sphere_"):
        sphere = data.replace("sphere_", "")
        bot.answer_callback_query(call.id)
        
        sprint = storage.get_waiting_sprint() or storage.get_active_sprint()
        if sprint:
            task_count = storage.get_user_task_count_by_sphere(user_id, sprint["id"], sphere)
            if task_count >= TASKS_PER_SPHERE:
                bot.send_message(
                    call.message.chat.id,
                    f"❌ У тебя уже есть {TASKS_PER_SPHERE} задачи по сфере '{sphere}'!\n"
                    f"Максимум: {TASKS_PER_SPHERE} задачи на сферу.",
                    reply_markup=spheres_keyboard()
                )
                return
        
        bot.send_message(
            call.message.chat.id,
            f"🌍 Куда направим фокус?\n\n"
            f"Выбрана сфера: <b>{sphere}</b>\n\n"
            f"📌 Это задача #{storage.get_user_task_count_by_sphere(user_id, sprint['id'], sphere) + 1} из {TASKS_PER_SPHERE} по этой сфере.\n\n"
            f"Теперь выбери сложность:",
            reply_markup=complexity_keyboard(),
            parse_mode="HTML"
        )
        return

    if data.startswith("complexity_"):
        complexity = data.replace("complexity_", "")
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            f"⚡ Отлично!\n\n"
            f"Выбрана сложность: <b>{complexity}</b>\n\n"
            f"✍️ Опиши задачу:\n\n"
            f"Напиши, что именно ты сделаешь в этой сфере.\n"
            f"Чёткая цель = ясный результат. 🎯",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_description_step, complexity)
        return

    if data.startswith("status_"):
        parts = data.split("_")
        if len(parts) >= 3:
            task_id = int(parts[1])
            status = "_".join(parts[2:])
            if storage.update_task_status(task_id, status):
                task = storage.get_task(task_id)
                bot.edit_message_text(
                    f"✅ Статус обновлён!\n\n{format_task_card(task)}\n\nТы приближаешься к цели. Ещё немного! 🔥",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=back_button(),
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text("❌ Не удалось обновить статус", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return

    if data.startswith("delete_"):
        task_id = int(data.replace("delete_", ""))
        storage.delete_task(task_id)
        bot.edit_message_text("🗑️ Задача удалена", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return

    if data.startswith("task_"):
        task_id = int(data.replace("task_", ""))
        task = storage.get_task(task_id)
        if task:
            bot.edit_message_text(
                f"{format_task_card(task)}\n\n📌 Выбери статус:\n\n"
                f"⏳ Не начата — пока просто идея\n"
                f"🔄 Начата — первый шаг сделан\n"
                f"⚡ В процессе — уже в движении\n"
                f"📈 Почти готова — финиш близко\n"
                f"✅ Выполнена — победа! 🎉\n\n"
                f"Где ты сейчас? Отметь — и двигайся дальше. 🚀",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=task_statuses_keyboard(task_id),
                parse_mode="HTML"
            )
        else:
            bot.edit_message_text("❌ Задача не найдена", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return

    if data.startswith("vote_"):
        parts = data.split("_")
        if len(parts) >= 3:
            sprint_id = int(parts[1])
            candidate_id = int(parts[2])
            if candidate_id == user_id:
                bot.edit_message_text("❌ Нельзя голосовать за себя!", call.message.chat.id, call.message.message_id, reply_markup=back_button())
                return
            existing_vote = storage.get_user_vote(sprint_id, user_id)
            if existing_vote:
                candidate = storage.get_user(existing_vote["candidate_id"])
                bot.edit_message_text(f"❌ Ты уже голосовал(а)!\n\nТвой голос отдан за: {candidate['full_name']}", call.message.chat.id, call.message.message_id, reply_markup=back_button())
                return
            storage.create_vote(sprint_id, user_id, candidate_id)
            candidate = storage.get_user(candidate_id)
            bot.edit_message_text(
                f"✅ Голос учтён!\n\n"
                f"⭐ Ты проголосовал(а) за: <b>{candidate['full_name']}</b>\n\n"
                f"Спасибо за участие! Твой голос — часть общей атмосферы 🌟",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_button(),
                parse_mode="HTML"
            )
        return


def process_description_step(message, complexity):
    user_id = message.from_user.id
    description = message.text.strip()
    
    if len(description) < 3:
        bot.send_message(message.chat.id, "❌ Описание должно содержать минимум 3 символа. Попробуй снова:")
        bot.register_next_step_handler(message, process_description_step, complexity)
        return
    
    waiting_sprint = storage.get_waiting_sprint()
    active_sprint = storage.get_active_sprint()
    
    if waiting_sprint and not is_sprint_active():
        sprint = waiting_sprint
        is_draft = True
    else:
        sprint = active_sprint
        is_draft = False
    
    if not sprint:
        bot.send_message(message.chat.id, "❌ Нет активного спринта!", reply_markup=main_menu())
        return
    
    sphere = "Здоровье"
    task_count_in_sphere = storage.get_user_task_count_by_sphere(user_id, sprint["id"], sphere)
    if task_count_in_sphere >= TASKS_PER_SPHERE:
        bot.send_message(
            message.chat.id,
            f"❌ По сфере '{sphere}' уже создано {TASKS_PER_SPHERE} задач!\n"
            f"Максимум: {TASKS_PER_SPHERE} задачи на сферу.",
            reply_markup=main_menu()
        )
        return
    
    task = storage.create_task(user_id, sprint["id"], sphere, description, complexity, is_draft)
    
    if is_draft:
        bot.send_message(
            message.chat.id,
            f"📝 Задача сохранена как черновик!\n\n{format_task_card(task)}\n\n"
            f"⏳ Она станет активной, когда спринт начнётся.\n"
            f"📌 Осталось задач по этой сфере: {TASKS_PER_SPHERE - task_count_in_sphere - 1}\n\n"
            f"Ты на шаг ближе к балансу. Продолжай! 💫",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"✅ Задача создана!\n\n{format_task_card(task)}\n\n"
            f"📌 Осталось задач по этой сфере: {TASKS_PER_SPHERE - task_count_in_sphere - 1}\n\n"
            f"Ты на шаг ближе к балансу. Продолжай! 💫",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


# ==================== ФУНКЦИИ ОТОБРАЖЕНИЯ ====================
def show_wheel(call):
    user_id = call.from_user.id
    active_sprint = storage.get_active_sprint()
    if not active_sprint:
        bot.edit_message_text("❌ Нет активного спринта", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return
    
    progress = get_user_sphere_progress(user_id, active_sprint["id"])
    summary = get_user_sphere_summary(user_id, active_sprint["id"])
    wheel = get_wheel_visual(progress)
    
    total_tasks = storage.get_user_task_count(user_id, active_sprint["id"])
    completed = len([t for t in storage.get_user_tasks(user_id, active_sprint["id"]) if t["status"] == TaskStatus.COMPLETED])
    avg_progress = sum(progress.values()) / len(progress) if progress else 0
    
    message = (
        f"🌀 Твоё Колесо баланса\n\n"
        f"Спринт #{active_sprint['number']}\n"
        f"📊 Прогресс: {completed}/{total_tasks} задач\n"
        f"📈 Средний уровень: {avg_progress:.0f}%\n\n"
        f"<code>{wheel}</code>\n\n"
        f"📊 Детали по сферам:\n"
        f"{summary}\n\n"
        f"Двигайся вперёд — каждый процент имеет значение! 🌱"
    )
    
    bot.edit_message_text(
        message,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_button(),
        parse_mode="HTML"
    )


def show_my_tasks(call):
    user_id = call.from_user.id
    active_sprint = storage.get_active_sprint()
    if not active_sprint:
        bot.edit_message_text("❌ Нет активного спринта", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return
    
    tasks = storage.get_user_tasks(user_id, active_sprint["id"])
    if not tasks:
        bot.edit_message_text(
            f"📭 У тебя пока нет задач на этот спринт.\n\n"
            f"Нужно поставить {TASKS_PER_SPHERE} задачи на каждую из {len(SPHERES)} сфер.\n"
            f"Всего: {MAX_TASKS_PER_USER} задач.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )
        return
    
    tasks_by_sphere = {}
    for sphere in SPHERES:
        tasks_by_sphere[sphere["name"]] = []
    for task in tasks:
        if task["sphere"] in tasks_by_sphere:
            tasks_by_sphere[task["sphere"]].append(task)
    
    message = f"📋 Твои задачи\n\n📅 Спринт #{active_sprint['number']}\n⏳ Осталось дней: {(datetime.fromisoformat(active_sprint['end_date']) - datetime.now()).days}\n\n"
    
    total_points = 0
    for sphere in SPHERES:
        sphere_tasks = tasks_by_sphere.get(sphere["name"], [])
        completed = len([t for t in sphere_tasks if t["status"] == TaskStatus.COMPLETED])
        message += f"{sphere['emoji']} <b>{sphere['name']}</b> ({completed}/{len(sphere_tasks)})\n"
        
        for task in sphere_tasks:
            message += f"   {format_task_card(task)}\n"
            progress = TaskStatus.PROGRESS.get(task["status"], 0)
            max_points = Complexity.POINTS.get(task["complexity"], 1)
            total_points += max_points * (progress / 100)
        message += "\n"
    
    message += f"💪 Итого баллов: {total_points:.1f}\n\nТы уже в движении. Остальное — вопрос времени и фокуса. 🔥"
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for t in tasks[:5]:
        keyboard.add(telebot.types.InlineKeyboardButton(f"✏️ #{t['id']} {t['description'][:20]}...", callback_data=f"task_{t['id']}"))
    keyboard.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="HTML")


def show_team_members(call):
    users = storage.get_all_users()
    if not users:
        bot.edit_message_text("👥 Пока нет зарегистрированных участников.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    
    message = "👥 Командный пульс\n\n"
    active_sprint = storage.get_active_sprint()
    
    for user in users:
        message += f"• {user['full_name']}"
        if active_sprint:
            tasks = storage.get_user_tasks(user["id"], active_sprint["id"])
            completed = len([t for t in tasks if t["status"] == TaskStatus.COMPLETED])
            total = len(tasks)
            progress = 0
            if tasks:
                progress = sum(TaskStatus.PROGRESS.get(t["status"], 0) for t in tasks) / len(tasks)
            message += f" — {completed}/{total} задач, {progress:.0f}%"
        message += "\n"
    
    if not is_sprint_active():
        waiting_sprint = storage.get_waiting_sprint()
        if waiting_sprint:
            message += f"\n⏳ До старта: {get_time_until_start()}"
    else:
        message += "\n\nВместе мы сильнее. Поддерживай, вдохновляй, двигайся в ритме команды! 🤝"
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=back_button(), parse_mode="HTML")


def show_sprint_status(call):
    active_sprint = storage.get_active_sprint()
    if not active_sprint:
        bot.edit_message_text("❌ Нет активного спринта", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return
    
    all_tasks = storage.get_sprint_tasks(active_sprint["id"])
    users = storage.get_all_users()
    
    message = f"📊 Пульс спринта #{active_sprint['number']}\n\n"
    message += f"📅 {datetime.fromisoformat(active_sprint['start_date']).strftime('%d.%m.%Y')} — {datetime.fromisoformat(active_sprint['end_date']).strftime('%d.%m.%Y')}\n"
    message += f"⏳ Осталось: {(datetime.fromisoformat(active_sprint['end_date']) - datetime.now()).days} дней\n\n"
    
    message += "👥 Участники и прогресс:\n"
    for user in users:
        user_tasks = [t for t in all_tasks if t["user_id"] == user["id"]]
        if user_tasks:
            completed = len([t for t in user_tasks if t["status"] == TaskStatus.COMPLETED])
            points = 0
            for t in user_tasks:
                progress = TaskStatus.PROGRESS.get(t["status"], 0)
                max_p = Complexity.POINTS.get(t["complexity"], 1)
                points += max_p * (progress / 100)
            message += f"• {user['full_name']}: {completed}/{len(user_tasks)} задач, {points:.1f} баллов\n"
    
    message += f"\n📈 Общая картина:\n"
    message += f"• Всего задач: {len(all_tasks)}\n"
    if all_tasks:
        completed = len([t for t in all_tasks if t["status"] == TaskStatus.COMPLETED])
        progress = sum(TaskStatus.PROGRESS.get(t["status"], 0) for t in all_tasks) / len(all_tasks)
        message += f"• Выполнено: {completed}\n"
        message += f"• Средний прогресс: {progress:.0f}%\n"
    
    message += "\nКаждый день приближает нас к общей цели! 🌟"
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=back_button(), parse_mode="HTML")


def start_create_task(call):
    waiting_sprint = storage.get_waiting_sprint()
    active_sprint = storage.get_active_sprint()
    
    sprint = waiting_sprint if waiting_sprint and not is_sprint_active() else active_sprint
    
    if not sprint:
        bot.edit_message_text("❌ Нет активного спринта", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return
    
    user_id = call.from_user.id
    total_tasks = storage.get_user_task_count(user_id, sprint["id"])
    if total_tasks >= MAX_TASKS_PER_USER:
        bot.edit_message_text(
            f"❌ Ты уже создал(а) все {MAX_TASKS_PER_USER} задач!\n"
            f"По {TASKS_PER_SPHERE} задачи на каждую из {len(SPHERES)} сфер.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )
        return
    
    intro_text = (
        "🌟 <b>Колесо баланса</b>\n\n"
        "Представь, что твоя жизнь — это колесо. Чтобы оно катилось ровно и быстро, "
        "все его части должны быть накачаны одинаково.\n\n"
        "В этом спринте мы прокачаем <b>7 сфер</b>, которые влияют на твоё ощущение счастья и гармонии:\n\n"
        "🏥 <b>Здоровье</b> — энергия, сила, самочувствие\n"
        "💼 <b>Карьера</b> — дело, которое приносит доход и реализацию\n"
        "💰 <b>Финансы</b> — свобода, накопления, разумные траты\n"
        "💕 <b>Отношения</b> — любовь, партнёрство, близость\n"
        "👨‍👩‍👧‍👦 <b>Семья</b> — поддержка, связь с родными, общие традиции\n"
        "🎨 <b>Хобби</b> — радость, творчество, время для себя\n"
        "📚 <b>Саморазвитие</b> — знания, навыки, личный рост\n\n"
        "По <b>2 задачи</b> на каждую сферу — и твоё колесо станет ещё круглее! 🌀\n\n"
        "Готов? Выбери, с чего начнём! 🚀"
    )
    
    # Отправляем картинку по ссылке + текст
    try:
        bot.send_photo(
            call.message.chat.id,
            photo="https://raw.githubusercontent.com/Anastaredko/valkiriibot/main/images/3.png",
            caption=intro_text,
            reply_markup=spheres_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Не удалось отправить картинку колеса: {e}")
        bot.edit_message_text(
            intro_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=spheres_keyboard(),
            parse_mode="HTML"
        )

def start_voting(call):
    user_id = call.from_user.id
    voting_sprint = storage.get_voting_sprint()
    if not voting_sprint:
        current_sprint = storage.get_current_sprint()
        if not current_sprint:
            bot.edit_message_text("❌ Нет активного спринта", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
            return
        if current_sprint["status"] == SprintStatus.ACTIVE:
            days_left = (datetime.fromisoformat(current_sprint['end_date']) - datetime.now()).days
            bot.edit_message_text(f"⏳ Спринт ещё не закончился!\nОсталось {days_left} дней.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
            return
        if current_sprint["status"] == SprintStatus.FINISHED:
            bot.edit_message_text("❌ Голосование уже завершено.\nИтоги в разделе 'Итоги спринта'.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
            return
        bot.edit_message_text("❌ Голосование недоступно", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    
    if voting_sprint.get("voting_end_date"):
        voting_end = datetime.fromisoformat(voting_sprint["voting_end_date"])
        if datetime.now() > voting_end:
            bot.edit_message_text("⏰ Время голосования истекло.\nРезультаты в разделе 'Итоги спринта'.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
            return
    
    existing_vote = storage.get_user_vote(voting_sprint["id"], user_id)
    if existing_vote:
        candidate = storage.get_user(existing_vote["candidate_id"])
        bot.edit_message_text(f"✅ Ты уже проголосовал(а)!\n\nТвой голос за: <b>{candidate['full_name']}</b>", call.message.chat.id, call.message.message_id, reply_markup=back_button(), parse_mode="HTML")
        return
    
    users = storage.get_all_users()
    candidates = [{"user_id": u["id"], "full_name": u["full_name"]} for u in users if u["id"] != user_id]
    if not candidates:
        bot.edit_message_text("❌ Нет других участников", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    
    message = f"⭐ <b>Звезда спринта</b>\n\n"
    message += f"Спринт #{voting_sprint['number']}\n"
    message += f"⏳ Голосование до {datetime.fromisoformat(voting_sprint['voting_end_date']).strftime('%H:%M %d.%m.%Y')}\n\n"
    message += f"Выбери человека, который, по твоему мнению, лучше всех проявил себя в этом спринте.\n\n"
    message += f"⚠️ <b>Важно:</b>\n"
    message += f"• Голос анонимный\n"
    message += f"• Нельзя голосовать за себя\n"
    message += f"• Только 1 голос\n\n"
    message += f"Твой выбор — признание чужих усилий. 🤝"
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=voting_keyboard(candidates, voting_sprint["id"]), parse_mode="HTML")


def show_sprint_results(call):
    finished_sprint = storage.get_last_finished_sprint()
    voting_sprint = storage.get_voting_sprint()
    
    if not finished_sprint and not voting_sprint:
        active_sprint = storage.get_active_sprint()
        if active_sprint:
            days_left = (datetime.fromisoformat(active_sprint['end_date']) - datetime.now()).days
            bot.edit_message_text(f"⏳ Спринт ещё не закончился!\nОсталось {days_left} дней.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
            return
        bot.edit_message_text("❌ Нет завершенных спринтов", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        return
    
    if voting_sprint:
        voting_end = datetime.fromisoformat(voting_sprint["voting_end_date"])
        if datetime.now() < voting_end:
            hours_left = int((voting_end - datetime.now()).total_seconds() / 3600)
            bot.edit_message_text(f"⏳ Итоги после голосования.\nОсталось {hours_left} часов.", call.message.chat.id, call.message.message_id, reply_markup=back_button())
            return
    
    sprint_to_show = finished_sprint or voting_sprint
    results = storage.get_sprint_results(sprint_to_show["id"])
    if not results:
        bot.edit_message_text("❌ Нет данных", call.message.chat.id, call.message.message_id, reply_markup=back_button())
        return
    
    message = f"🏆 <b>Итоги спринта #{sprint_to_show['number']}</b> 🏆\n\n"
    message += f"📅 {datetime.fromisoformat(sprint_to_show['start_date']).strftime('%d.%m.%Y')} — {datetime.fromisoformat(sprint_to_show['end_date']).strftime('%d.%m.%Y')}\n\n"
    message += "═══════════════════════════════════\n\n"
    
    if results and results[0]["is_winner"]:
        winner = results[0]
        message += f"⭐ <b>Звезда спринта:</b> {winner['full_name']}\n"
        message += f"   🎯 Баллы за задачи: {winner['task_points']:.1f}\n"
        message += f"   🗳️ Голосов: {winner['vote_count']}\n"
        message += f"   💯 Итоговый счёт: {winner['total_points']:.1f}\n\n"
        message += "═══════════════════════════════════\n\n"
    
    message += "📊 <b>Таблица результатов:</b>\n\n"
    for i, result in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        message += f"{medal} <b>{result['full_name']}</b>\n"
        message += f"   📋 Задач: {len(result['tasks'])} | Баллы: {result['task_points']:.1f}\n"
        message += f"   🗳️ Голосов: {result['vote_count']} | Итого: {result['total_points']:.1f}\n\n"
    
    message += "═══════════════════════════════════\n"
    message += "📋 <b>Детали по задачам:</b>\n\n"
    
    for result in results:
        if result['tasks']:
            message += f"<b>{result['full_name']}</b> (баллов: {result['task_points']:.1f}, голосов: {result['vote_count']}):\n"
            tasks_by_sphere = {}
            for sphere in SPHERES:
                tasks_by_sphere[sphere["name"]] = []
            for task in result['tasks']:
                if task["sphere"] in tasks_by_sphere:
                    tasks_by_sphere[task["sphere"]].append(task)
            
            for sphere in SPHERES:
                sphere_tasks = tasks_by_sphere.get(sphere["name"], [])
                if sphere_tasks:
                    message += f"   {sphere['emoji']} {sphere['name']}:\n"
                    for task in sphere_tasks:
                        progress = TaskStatus.PROGRESS.get(task["status"], 0)
                        max_points = Complexity.POINTS.get(task["complexity"], 1)
                        points = max_points * (progress / 100)
                        message += f"      • {get_status_emoji(task['status'])} {task['description']} — {points:.1f} баллов\n"
            message += "\n"
    
    message += "Спринт пройден. Опыт получен. Баланс прокачан.\n"
    message += "До встречи в следующем рывке! 🚀"
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=back_button(), parse_mode="HTML")


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    import threading
    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def health_check():
        return "Бот жив!", 200

    def run_flask():
        app.run(host='0.0.0.0', port=8080)

    threading.Thread(target=run_flask, daemon=True).start()

    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"📅 Старт спринта: {SPRINT_START.strftime('%d.%m.%Y %H:%M')}")
    print(f"⏳ До старта: {get_time_until_start()}")
    print(f"📌 На спринт: {TASKS_PER_SPHERE} задачи на каждую из {len(SPHERES)} сфер = {MAX_TASKS_PER_USER} задач")
    print("✅ Версия: финальная с обновлёнными текстами")
    print("📍 Жду сообщения...")

    bot.infinity_polling()