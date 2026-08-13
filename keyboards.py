# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import SPHERES

class Keyboards:
    """Все клавиатуры бота"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = [
            [InlineKeyboardButton("📋 Мои задачи", callback_data="my_tasks")],
            [InlineKeyboardButton("👥 Задачи команды", callback_data="team_tasks")],
            [InlineKeyboardButton("➕ Создать задачу", callback_data="create_task")],
            [InlineKeyboardButton("📊 Статус спринта", callback_data="sprint_status")],
            [InlineKeyboardButton("⭐ Проголосовать", callback_data="vote")],
            [InlineKeyboardButton("🏆 Итоги спринта", callback_data="sprint_results")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def spheres() -> InlineKeyboardMarkup:
        """Выбор сферы жизни"""
        keyboard = []
        for sphere in SPHERES:
            keyboard.append([
                InlineKeyboardButton(f"🏷️ {sphere}", callback_data=f"sphere_{sphere}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def complexity() -> InlineKeyboardMarkup:
        """Выбор сложности"""
        keyboard = [
            [
                InlineKeyboardButton("🟢 Легкая (1 балл)", callback_data="complexity_легкая"),
                InlineKeyboardButton("🟡 Средняя (2 балла)", callback_data="complexity_средняя")
            ],
            [
                InlineKeyboardButton("🔴 Сложная (3 балла)", callback_data="complexity_сложная")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_statuses(task_id: int) -> InlineKeyboardMarkup:
        """Изменение статуса задачи"""
        keyboard = [
            [
                InlineKeyboardButton("⏳ Не начата (0%)", callback_data=f"status_{task_id}_не начата"),
                InlineKeyboardButton("🔄 Начата (25%)", callback_data=f"status_{task_id}_начата")
            ],
            [
                InlineKeyboardButton("⚡ В процессе (50%)", callback_data=f"status_{task_id}_в процессе"),
                InlineKeyboardButton("📈 Почти готова (75%)", callback_data=f"status_{task_id}_почти готова")
            ],
            [
                InlineKeyboardButton("✅ Выполнена (100%)", callback_data=f"status_{task_id}_выполнена")
            ],
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{task_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="my_tasks")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def voting_candidates(candidates: list, sprint_id: int) -> InlineKeyboardMarkup:
        """Список кандидатов для голосования"""
        keyboard = []
        for user in candidates:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {user['full_name']}",
                    callback_data=f"vote_{sprint_id}_{user['user_id']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button() -> InlineKeyboardMarkup:
        """Кнопка Назад"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ])