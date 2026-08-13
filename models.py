# models.py

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, List

class Complexity:
    """Сложность задачи"""
    EASY = "легкая"
    MEDIUM = "средняя"
    HARD = "сложная"
    
    POINTS = {
        EASY: 1,
        MEDIUM: 2,
        HARD: 3
    }
    
    @classmethod
    def get_points(cls, complexity: str) -> int:
        return cls.POINTS.get(complexity, 1)

class TaskStatus:
    """Статус задачи"""
    NOT_STARTED = "не начата"
    STARTED = "начата"
    IN_PROGRESS = "в процессе"
    ALMOST_DONE = "почти готова"
    COMPLETED = "выполнена"
    FAILED = "провалена"
    
    # Прогресс в процентах для каждого статуса
    PROGRESS = {
        NOT_STARTED: 0,
        STARTED: 25,
        IN_PROGRESS: 50,
        ALMOST_DONE: 75,
        COMPLETED: 100,
        FAILED: 0
    }
    
    # Статусы, доступные для выбора пользователем
    USER_STATUSES = [
        NOT_STARTED,
        STARTED,
        IN_PROGRESS,
        ALMOST_DONE,
        COMPLETED
    ]
    
    @classmethod
    def get_progress(cls, status: str) -> int:
        return cls.PROGRESS.get(status, 0)

class SprintStatus:
    """Статус спринта"""
    ACTIVE = "active"
    VOTING = "voting"
    FINISHED = "finished"

@dataclass
class User:
    """Модель пользователя"""
    id: int
    username: str
    full_name: str
    registered_at: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Sprint:
    """Модель спринта"""
    id: int
    number: int
    start_date: str
    end_date: str
    status: str
    voting_end_date: Optional[str] = None
    winner_id: Optional[int] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def is_active(self) -> bool:
        return self.status == SprintStatus.ACTIVE
    
    def is_voting(self) -> bool:
        return self.status == SprintStatus.VOTING
    
    def is_finished(self) -> bool:
        return self.status == SprintStatus.FINISHED
    
    def days_left(self) -> int:
        if not self.is_active():
            return 0
        end = datetime.fromisoformat(self.end_date)
        return max(0, (end - datetime.now()).days)

@dataclass
class Task:
    """Модель задачи"""
    id: int
    user_id: int
    sprint_id: int
    sphere: str
    description: str
    complexity: str
    status: str
    created_at: str
    updated_at: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def get_points(self) -> float:
        """Рассчитать баллы за задачу на основе статуса и сложности"""
        progress = TaskStatus.get_progress(self.status)
        max_points = Complexity.get_points(self.complexity)
        return max_points * (progress / 100)
    
    def get_max_points(self) -> int:
        return Complexity.get_points(self.complexity)

@dataclass
class Vote:
    """Модель голоса"""
    id: int
    sprint_id: int
    voter_id: int
    candidate_id: int
    created_at: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class SprintResult:
    """Результаты участника в спринте"""
    user_id: int
    full_name: str
    tasks: List[Task]
    task_points: float
    vote_count: int
    total_points: float
    is_winner: bool = False