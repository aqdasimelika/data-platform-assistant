from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from faq_loader import FAQLoader
from conversation_manager import ConversationManager
from search_engine import search_current_node_options,search_all_options,get_path_from_parent
from suggestion_engine import suggest_from_path
from ticket_manager import TicketManager
from role_client import get_windows_username, fetch_role_from_service
from models import Step

app = Flask(__name__, static_folder=None)
CORS(app, resources={
    r"/*": {
        "origins": ["http://127.0.0.1:5500"]
    }
})
BASE = os.path.dirname(__file__)

faq_loader = FAQLoader(path_template='faq/faq_{}.json')
conv = ConversationManager()
ticket_mgr = TicketManager(store_path='../data/tickets_log.json')

# helper
def get_role_for_user(username):
    # in real: call external service; here mock
    return fetch_role_from_service(username)

@app.route('/role_detect', methods=['POST'])
def role_detect():
    data = request.get_json() or {}
    username = data.get('username') or get_windows_username()
    role = get_role_for_user(username)
    return jsonify({'username': username, 'role': role})

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json() or {}
    user_id = data.get('user_id','guest')
    username = data.get('username') or get_windows_username()
    role = data.get('role') or get_role_for_user(username)
    conv.init_user(user_id)
    conv.set_role(user_id, role)
    # load faq and start node
    faq = faq_loader.load(role if role else 'expert')
    start_node = faq.get('startNode')
    conv.start(user_id, start_node)
    node = faq_loader.get_node(role, start_node)
    node['id'] = start_node
    return jsonify({'role': role, 'node': node})


@app.route('/faq', methods=['POST'])
def faq_action():
    data = request.get_json() or {}
    user_id = data.get('user_id', 'guest')
    action = data.get('action', 'get')

    ctx = conv.get_ctx(user_id) or {}
    role = ctx.get('role') or data.get('role') or 'expert'

    faq_data = faq_loader.load(role)
    node_id = data.get('node') or conv.current_node(user_id)

    # -------- GET --------
    if action == 'get':
        if not node_id:
            node_id = faq_data.get('startNode')
            conv.reset(user_id, node_id)

        node_data = faq_loader.get_node(role, node_id)
        node_data['id'] = node_id
        return jsonify(node_data)

    # -------- SELECT --------
    if action == 'select':
        selected = data.get('selected')
        if not selected:
            return jsonify({'error': 'selected required'}), 400

        next_node = selected.get('next')
        label = selected.get('label')

        if not next_node:
            return jsonify({'error': 'next missing'}), 400
        
        path = selected.get('path')
        if path:
            conv.rebuild_path(user_id, path, faq_data['nodes'])
        else:
    # اگر مسیر پیدا نشد، فقط search رو ذخیره کن
            conv.record_search(user_id, label, next_node)
        node_data = faq_loader.get_node(role, next_node)
        node_data['id'] = next_node
        return jsonify(node_data)
         

    if action == 'input':
        node_id = data.get('node')
        value = data.get('value')

        if not node_id or value is None:
            return jsonify({'error': 'node and value required'}), 400

        node_info = faq_loader.get_node(role, node_id)
        next_node = node_info.get('next')

        # ثبت ورودی
        conv.record_input(
            user_id=user_id,
            from_node=node_id,
            value=value,
            to_node=next_node
        )

        if not next_node:
            return jsonify({'error': 'no next node'}), 400

        node_data = faq_loader.get_node(role, next_node)
        node_data['id'] = next_node
        return jsonify(node_data)



    

    # -------- LOAD MORE --------
    if action == 'load_more':
        page = int(data.get('page', 1))
        node_info = faq_loader.get_node(role, node_id)

        options = node_info.get('options', [])
        page_size = node_info.get('maxVisibleOptions', 4)

        start = (page - 1) * page_size
        chunk = options[start:start + page_size]

        return jsonify({
            'options': chunk,
            'page': page,
            'total': len(options)
        })
        
    if action == 'restart':
        start_node = faq_data.get('startNode')

        conv.start(user_id, start_node)   # ← این خیلی مهمه

        node_data = faq_loader.get_node(role, start_node)
        node_data['id'] = start_node
        return jsonify(node_data)

    # -------- BACK --------
    if action == 'back':
        prev_node = conv.go_back(user_id)

        if not prev_node:
            return jsonify({'error': 'no previous node'}), 400

        node_data = faq_loader.get_node(role, prev_node)
        node_data['id'] = prev_node
        return jsonify(node_data)


    return jsonify({'error': 'unknown action'}), 400


@app.route('/search', methods=['POST'])
def search_route():
    data = request.get_json() or {}
    user_id = data.get('user_id', 'guest')
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'results': []})
    ctx = conv.get_ctx(user_id)
    role = ctx.get('role')
    faq = faq_loader.load(role)
    current_node = conv.current_node(user_id)
    # فقط گزینه‌ها جستجو شوند (نه messageها)
    results = search_current_node_options(faq, current_node, query)
    if results:
        # برای هر نتیجه، مسیر با parent محاسبه شود
        for item in results:
            item['path'] = get_path_from_parent(faq['nodes'], item['node'])
        return jsonify({'results': results, 'source': 'current_node'})
    results = search_all_options(faq, query)
    if results:
        for item in results:
            item['path'] = get_path_from_parent(faq['nodes'], item['node'])
        return jsonify({'results': results, 'source': 'global'})
    return jsonify({'results': [], 'message': 'لطفاً مراحل را طی کنید'})


@app.route('/suggest', methods=['POST'])
def suggest_route():
    data = request.get_json() or {}
    user_id = data.get('user_id','guest')
    path = conv.get_path(user_id)
    suggestion = suggest_from_path(path)
    return jsonify({'suggestion': suggestion})

@app.route('/ticket/preview', methods=['GET'])
def preview_ticket():
    user_id = request.args.get('user_id','guest')
    username = request.args.get('username') or get_windows_username()
    role = conv.get_ctx(user_id).get('role') or fetch_role_from_service(username)
    path = conv.get_path(user_id)
    inputs = [p for p in path if p['type']=='input']
    ticket = ticket_mgr.prepare_ticket(username, role, path, inputs)
    return jsonify({'preview': ticket})


@app.route('/ticket/form', methods=['POST'])
def ticket_form():
    data = request.get_json() or {}
    user_id = data.get('user_id','guest')

    conv.record_input(user_id, 'description', data.get('description'))
    conv.record_input(user_id, 'serial', data.get('serial'))
    conv.record_input(user_id, 'log_path', data.get('log_path'))

    return jsonify({'status':'ok'})


@app.route('/ticket/confirm', methods=['POST'])
def confirm_ticket():
    data = request.get_json() or {}
    user_id = data.get('user_id','guest')
    username = data.get('username') or get_windows_username()
    role = conv.get_ctx(user_id).get('role') or fetch_role_from_service(username)
    path = conv.get_path(user_id)
    inputs = [p for p in path if p['type']=='input']
    ticket = ticket_mgr.prepare_ticket(username, role, path, inputs)
    saved = ticket_mgr.save_local(ticket)
    return jsonify({'status':'ok',
                    'ticket': saved,
                    'ticket_id': saved.get('id')})


if __name__ == '__main__':
    app.run(debug=True, port=5000)

