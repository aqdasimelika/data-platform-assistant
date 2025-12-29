# simple keyword-based suggestion engine
RULES = [
    (['disk','io','write','دیسک','ذخیره'], 'hardware_root'),
    (['plugin','پلاگین','cache','ذخیره موقت'], 'plugin_root'),
    (['oracle','ora','ORA-'], 'database_root')
]

def suggest_from_path(path_steps):
    text = ' '.join([ (s.get('label') or s.get('value') or '') for s in path_steps ]).lower()
    for keywords, target in RULES:
        for kw in keywords:
            if kw.lower() in text:
                return {'message': f'به نظر می‌رسد مشکل مرتبط با {target} باشد.', 'target': target}
    return None
