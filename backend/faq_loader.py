import json
import threading
import os

class FAQLoader:
    def __init__(self, path_template='/faq/faq_{}.json'):
        self.path_template = path_template
        self.lock = threading.RLock()
        self.cache = {}

    def load(self, role):
        with self.lock:
            if role in self.cache:
                return self.cache[role]

            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, self.path_template.format(role))

            print("FAQ PATH =>", path)  # 👈 برای دیباگ

            if not os.path.exists(path):
                raise FileNotFoundError(path)

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.cache[role] = data
            return data

    def get_node(self, role, node_id):
        data = self.load(role)
        return data['nodes'].get(node_id)
    def build_path_to_root(self, role, target_node):
        faq = self.load(role)
        nodes = faq.get('nodes', {})

        path = []
        current = target_node

        while current:
            path.append(current)
            parent = nodes.get(current, {}).get('parent')
            current = parent

        path.reverse()
        return path
    
    
    def get_path_between(self, role, from_node, to_node):
    # """
    # مسیر منطقی بین دو نود در درخت FAQ
    # """
        tree = self.load(role)
        nodes = tree['nodes']

        path = []
        current = from_node

        while current and current != to_node:
            path.append(current)
            next_node = nodes[current].get('next')
            if not next_node:
                break
            current = next_node

        path.append(to_node)
        return path
    def search(self, role, query):
        data = self.load(role)
        results = []

        for node_id, node in data['nodes'].items():
            text = (
                node.get('text', '') +
                node.get('question', '')
            )

            if query.lower() in text.lower():
                path = self.find_path(data, data['startNode'], node_id)
                if path:
                    results.append({
                        'title': text[:60],
                        'node': node_id,
                        'path': path
                    })

        return results
    
    def find_path(self, data, start, target):
        visited = set()

        def dfs(node_id, path):
            if node_id in visited:
                return None
            visited.add(node_id)

            if node_id == target:
                return path + [node_id]

            node = data['nodes'].get(node_id, {})
            for opt in node.get('options', []):
                res = dfs(opt['next'], path + [node_id])
                if res:
                    return res

            if node.get('next'):
                return dfs(node['next'], path + [node_id])

            return None

        return dfs(start, [])


