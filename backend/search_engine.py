def _match(text, q):
    return q.lower() in text.lower()
def search_options(options, query):
    q = query.strip().lower()
    results = []

    for opt in options:
        label = opt.get('label', '')
        if q in label.lower():
            results.append({
                'title': label,
                'node': opt.get('next')
            })

    return results


def search_current_node_options(faq, current_node_id, query):
    if not current_node_id:
        return []

    node = faq['nodes'].get(current_node_id)
    if not node:
        return []

    return search_options(node.get('options', []), query)

def search_all_options(faq, query):
    results = []
    q = query.lower()
    for node_id, node in faq['nodes'].items():
        for opt in node.get('options', []):
            label = opt.get('label', '')
            if q in label.lower():
                results.append({
                    'title': label,
                    'node': opt.get('next')
                })
    return results



def get_path_from_parent(nodes, target_node):
    """
    ساخت مسیر از target به عقب با استفاده از parent تا start.
    """
    path = []
    current = target_node
    while current:
        path.append(current)
        current = nodes.get(current, {}).get('parent')
    return path[::-1] if path else None  # معکوس برای از start به target

def find_path_to_node(nodes, start_node, target_node):
    from collections import deque

    queue = deque([(start_node, [])])
    visited = set()

    while queue:
        current, path = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if current == target_node:
            return path + [current]

        node = nodes.get(current)
        if not node:
            continue

        for opt in node.get('options', []):
            nxt = opt.get('next')
            if nxt:
                queue.append((nxt, path + [current]))

    return None

