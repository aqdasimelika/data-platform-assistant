import getpass
# This uses the same mock logic as before; replace with real HTTP call if provided
def get_windows_username():
    return getpass.getuser()

def fetch_role_from_service(username, service_url=None):
    # Mock rule: username starting with 'expert' or 'admin' => expert
    if username.lower().startswith('expert') or username.lower().startswith('admin'):
        return 'expert'
    return 'expert'
    # return 'inquiry'
