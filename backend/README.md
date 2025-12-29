1) نصب پایتون 3.8+
2) ساخت virtualenv:
   python -m venv venv
3) فعال‌سازی (PowerShell):
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\\venv\\Scripts\\activate
4) نصب نیازمندی‌ها:
   pip install -r requirements.txt
5) اجرا:
   cd backend
   python api_server.py
6) تست اولیه:
   POST http://127.0.0.1:5000/start  with JSON: {"user_id":"saba"}
   POST http://127.0.0.1:5000/faq  for actions (see API)
