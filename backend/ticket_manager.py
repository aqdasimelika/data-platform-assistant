import json, os
from datetime import datetime

class TicketManager:
    def __init__(self, store_path='../data/tickets_log.json'):
        self.store_path = os.path.join(os.path.dirname(__file__), store_path)
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        if not os.path.exists(self.store_path):
            with open(self.store_path,'w',encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load(self):
        with open(self.store_path,'r',encoding='utf-8') as f:
            return json.load(f)

    def _save(self, arr):
        with open(self.store_path,'w',encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, indent=2)

    def prepare_ticket(self, username, role, path, inputs):
        ticket = {
            'id': int(datetime.utcnow().timestamp()*1000),
            'username': username,
            'role': role,
            'path': path,
            'inputs': inputs,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        return ticket

    def save_local(self, ticket):
        arr = self._load()
        arr.append(ticket)
        self._save(arr)
        return ticket
