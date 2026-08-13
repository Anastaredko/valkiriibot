# storage.py

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models import User, Sprint, Task, Vote, SprintResult, SprintStatus, TaskStatus, Complexity

class Storage:
    """Менеджер хранения данных"""
    
    def __init__(self, file_path="data.json"):
        self.file_path = file_path
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Загрузить данные из файла"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._get_default_data()
    
    def _get_default_data(self) -> Dict:
        """Структура по умолчанию"""
        return {
            "users": {},
            "sprints": [],
            "tasks": [],
            "votes": [],
            "task_counter": 0,
            "vote_counter": 0,
            "sprint_counter": 0
        }
    
    def _save(self):
        """Сохранить данные в файл"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    # === РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ===
    
    def get_user(self, user_id: int) -> Optional[User]:
        user_data = self.data["users"].get(str(user_id))
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_all_users(self) -> List[User]:
        return [User.from_dict(data) for data in self.data["users"].values()]
    
    def create_user(self, user_id: int, username: str, full_name: str) -> User:
        if str(user_id) not in self.data["users"]:
            user = User(
                id=user_id,
                username=username or str(user_id),
                full_name=full_name,
                registered_at=datetime.now().isoformat()
            )
            self.data["users"][str(user_id)] = user.to_dict()
            self._save()
        return self.get_user(user_id)
    
    # === РАБОТА СО СПРИНТАМИ ===
    
    def get_active_sprint(self) -> Optional[Sprint]:
        for sprint_data in self.data["sprints"]:
            sprint = Sprint.from_dict(sprint_data)
            if sprint.is_active():
                return sprint
        return None
    
    def get_voting_sprint(self) -> Optional[Sprint]:
        for sprint_data in self.data["sprints"]:
            sprint = Sprint.from_dict(sprint_data)
            if sprint.is_voting():
                return sprint
        return None
    
    def get_current_sprint(self) -> Optional[Sprint]:
        for sprint_data in reversed(self.data["sprints"]):
            sprint = Sprint.from_dict(sprint_data)
            if sprint.is_active() or sprint.is_voting():
                return sprint
        return None
    
    def get_last_finished_sprint(self) -> Optional[Sprint]:
        for sprint_data in reversed(self.data["sprints"]):
            sprint = Sprint.from_dict(sprint_data)
            if sprint.is_finished():
                return sprint
        return None
    
    def get_sprint(self, sprint_id: int) -> Optional[Sprint]:
        for sprint_data in self.data["sprints"]:
            sprint = Sprint.from_dict(sprint_data)
            if sprint.id == sprint_id:
                return sprint
        return None
    
    def create_sprint(self) -> Sprint:
        self.data["sprint_counter"] += 1
        number = self.data["sprint_counter"]
        
        now = datetime.now()
        sprint = Sprint(
            id=int(now.timestamp()),
            number=number,
            start_date=now.isoformat(),
            end_date=(now + timedelta(days=14)).isoformat(),
            status=SprintStatus.ACTIVE
        )
        self.data["sprints"].append(sprint.to_dict())
        self._save()
        return sprint
    
    def update_sprint_status(self, sprint_id: int, status: str):
        for sprint_data in self.data["sprints"]:
            if sprint_data["id"] == sprint_id:
                sprint_data["status"] = status
                if status == SprintStatus.VOTING:
                    sprint_data["voting_end_date"] = (
                        datetime.now() + timedelta(hours=24)
                    ).isoformat()
                self._save()
                return True
        return False
    
    def set_sprint_winner(self, sprint_id: int, winner_id: int):
        for sprint_data in self.data["sprints"]:
            if sprint_data["id"] == sprint_id:
                sprint_data["winner_id"] = winner_id
                sprint_data["status"] = SprintStatus.FINISHED
                self._save()
                return True
        return False
    
    # === РАБОТА С ЗАДАЧАМИ ===
    
    def create_task(self, user_id: int, sprint_id: int, sphere: str,
                   description: str, complexity: str) -> Task:
        self.data["task_counter"] += 1
        now = datetime.now().isoformat()
        
        task = Task(
            id=self.data["task_counter"],
            user_id=user_id,
            sprint_id=sprint_id,
            sphere=sphere,
            description=description,
            complexity=complexity,
            status=TaskStatus.NOT_STARTED,
            created_at=now,
            updated_at=now
        )
        self.data["tasks"].append(task.to_dict())
        self._save()
        return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        for task_data in self.data["tasks"]:
            task = Task.from_dict(task_data)
            if task.id == task_id:
                return task
        return None
    
    def get_user_tasks(self, user_id: int, sprint_id: int) -> List[Task]:
        tasks = []
        for task_data in self.data["tasks"]:
            task = Task.from_dict(task_data)
            if task.user_id == user_id and task.sprint_id == sprint_id:
                tasks.append(task)
        return tasks
    
    def get_sprint_tasks(self, sprint_id: int) -> List[Task]:
        tasks = []
        for task_data in self.data["tasks"]:
            task = Task.from_dict(task_data)
            if task.sprint_id == sprint_id:
                tasks.append(task)
        return tasks
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        for task_data in self.data["tasks"]:
            if task_data["id"] == task_id:
                task_data["status"] = status
                task_data["updated_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False
    
    def delete_task(self, task_id: int) -> bool:
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        self._save()
        return True
    
    def get_user_task_count(self, user_id: int, sprint_id: int) -> int:
        return len(self.get_user_tasks(user_id, sprint_id))
    
    # === РАБОТА С ГОЛОСАМИ ===
    
    def create_vote(self, sprint_id: int, voter_id: int, candidate_id: int) -> Vote:
        self.data["vote_counter"] += 1
        vote = Vote(
            id=self.data["vote_counter"],
            sprint_id=sprint_id,
            voter_id=voter_id,
            candidate_id=candidate_id,
            created_at=datetime.now().isoformat()
        )
        self.data["votes"].append(vote.to_dict())
        self._save()
        return vote
    
    def get_user_vote(self, sprint_id: int, voter_id: int) -> Optional[Vote]:
        for vote_data in self.data["votes"]:
            vote = Vote.from_dict(vote_data)
            if vote.sprint_id == sprint_id and vote.voter_id == voter_id:
                return vote
        return None
    
    def get_candidate_votes(self, sprint_id: int, candidate_id: int) -> int:
        count = 0
        for vote_data in self.data["votes"]:
            vote = Vote.from_dict(vote_data)
            if vote.sprint_id == sprint_id and vote.candidate_id == candidate_id:
                count += 1
        return count
    
    def get_all_votes(self, sprint_id: int) -> List[Vote]:
        votes = []
        for vote_data in self.data["votes"]:
            vote = Vote.from_dict(vote_data)
            if vote.sprint_id == sprint_id:
                votes.append(vote)
        return votes
    
    # === РАСЧЕТ РЕЗУЛЬТАТОВ ===
    
    def calculate_sprint_results(self, sprint_id: int) -> List[SprintResult]:
        tasks = self.get_sprint_tasks(sprint_id)
        votes = self.get_all_votes(sprint_id)
        users = self.get_all_users()
        
        user_tasks: Dict[int, List[Task]] = {}
        for task in tasks:
            if task.user_id not in user_tasks:
                user_tasks[task.user_id] = []
            user_tasks[task.user_id].append(task)
        
        vote_counts: Dict[int, int] = {}
        for vote in votes:
            if vote.candidate_id not in vote_counts:
                vote_counts[vote.candidate_id] = 0
            vote_counts[vote.candidate_id] += 1
        
        results = []
        for user in users:
            if user.id in user_tasks:
                user_task_list = user_tasks[user.id]
                task_points = sum(t.get_points() for t in user_task_list)
                vote_count = vote_counts.get(user.id, 0)
                
                results.append(SprintResult(
                    user_id=user.id,
                    full_name=user.full_name,
                    tasks=user_task_list,
                    task_points=round(task_points, 1),
                    vote_count=vote_count,
                    total_points=round(task_points + vote_count, 1)
                ))
        
        results.sort(key=lambda x: x.total_points, reverse=True)
        
        if results:
            results[0].is_winner = True
        
        return results
    
    def get_sprint_results(self, sprint_id: int) -> Optional[List[SprintResult]]:
        sprint = self.get_sprint(sprint_id)
        if not sprint or sprint.is_active():
            return None
        return self.calculate_sprint_results(sprint_id)