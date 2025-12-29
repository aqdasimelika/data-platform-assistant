import threading
from models import Step

class ConversationManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.sessions = {}  # user_id -> context

    def init_user(self, user_id):
        with self.lock:
            if user_id not in self.sessions:
                self.sessions[user_id] = {
                    'user_id': user_id,
                    'role': None,
                    'stack': [],   # node ids visited (for current position)
                    'path': [],    # list of Step objects (history)
                }

    def get_ctx(self, user_id):
        self.init_user(user_id)
        return self.sessions[user_id]

    def set_role(self, user_id, role):
        ctx = self.get_ctx(user_id)
        ctx['role'] = role

    def start(self, user_id, start_node):
        ctx = self.get_ctx(user_id)
        ctx['stack'] = [start_node]
        ctx['path'] = []

    def current_node(self, user_id):
        ctx = self.get_ctx(user_id)
        return ctx['stack'][-1] if ctx['stack'] else None

    def record_select(self, user_id, from_node, label, to_node):
        ctx = self.get_ctx(user_id)
        # ذخیره انتخاب
        ctx['path'].append(
            Step(type='select', node=from_node, label=label)
        )
        # حرکت به نود بعدی
        ctx['stack'].append(to_node)

    def record_input(self, user_id, from_node, value, to_node):
        ctx = self.get_ctx(user_id)
        ctx['path'].append(
            Step(type='input', node=from_node, value=value)
        )
        if to_node != from_node:
            ctx['stack'].append(to_node)

    def record_search(self, user_id, query, matched_node):
        ctx = self.get_ctx(user_id)
        ctx['stack'].append(matched_node)
        ctx['path'].append(Step(type='search', node=matched_node, label=query))

    def record_suggest(self, user_id, from_node, to_node):
        ctx = self.get_ctx(user_id)
        ctx['stack'].append(to_node)
        ctx['path'].append(Step(type='suggest', node=to_node, label=f"from:{from_node}"))

    def go_back(self, user_id):
        ctx = self.get_ctx(user_id)
        if len(ctx['stack']) <= 1:
            return ctx['stack'][0] if ctx['stack'] else None
        ctx['stack'].pop()
        if ctx['path']:
            ctx['path'].pop()
        return ctx['stack'][-1]

    def reset(self, user_id, start_node):
        ctx = self.get_ctx(user_id)
        ctx['stack'] = [start_node]
        ctx['path'] = []

    def get_path(self, user_id):
        ctx = self.get_ctx(user_id)
        return [s.to_dict() for s in ctx['path']]

    def rebuild_path(self, user_id, nodes_path, faq_nodes):
        """
        بازسازی مسیر با استفاده از parent و استخراج label واقعی از options parent.
        """
        ctx = self.get_ctx(user_id)
        ctx['stack'] = nodes_path[:]
        ctx['path'] = []
        for i in range(len(nodes_path) - 1):
            from_node = nodes_path[i]
            to_node = nodes_path[i + 1]
            # استخراج label از options نود from
            node_data = faq_nodes.get(from_node, {})
            options = node_data.get('options', [])
            label = '(via search)'  # پیش‌فرض
            for opt in options:
                if opt.get('next') == to_node:
                    label = opt.get('label', '(via search)')
                    break
            ctx['path'].append(
                Step(type='select', node=from_node, label=label)
            )