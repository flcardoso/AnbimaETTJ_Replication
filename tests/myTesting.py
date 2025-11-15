import os
import json
import base64
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Set your credentials
# os.environ['ANBIMA_CLIENT_ID'] = "CLIENT_ID_HERE"
# os.environ['ANBIMA_CLIENT_SECRET'] = "CLIENT_SECRET_HERE"

client_id = os.environ.get('ANBIMA_CLIENT_ID', 'your_client_id')
client_secret = os.environ.get('ANBIMA_CLIENT_SECRET', 'your_client_secret')
auth_string = f'{client_id}:{client_secret}'
auth = base64.b64encode(auth_string.encode()).decode()

print("=" * 60)
print("ANBIMA API Testing Script (Python)")
print("=" * 60)

try:
    # 1. Get access token
    print("\n1. Getting access token...")
    auth_url = "https://api.anbima.com.br/oauth/access-token"
    auth_body = {"grant_type": "client_credentials"}
    auth_data = json.dumps(auth_body).encode('utf-8')

    auth_request = Request(auth_url, data=auth_data, method='POST')
    auth_request.add_header('Content-Type', 'application/json')
    auth_request.add_header('Authorization', f'Basic {auth}')

    with urlopen(auth_request) as auth_resp:
        print(f"   Status: {auth_resp.status}")
        auth_result = json.loads(auth_resp.read().decode('utf-8'))
        token = auth_result.get('access_token')
        print(f"   ✓ Access token obtained: {token[:20]}...")

    # 2. Use token to call ETTJ API
    print("\n2. Calling ETTJ API...")
    api_url = "https://api-sandbox.anbima.com.br/feed/precos-indices/v1/titulos-publicos/curvas-juros"

    api_request = Request(api_url)
    api_request.add_header('client_id', client_id)
    api_request.add_header('access_token', token)
    api_request.add_header('Authorization', f'Bearer {token}')

    with urlopen(api_request) as api_resp:
        print(f"   Status: {api_resp.status}")
        result = json.loads(api_resp.read().decode('utf-8'))
        print("   ✓ Data retrieved successfully!")

    # Print result
    print("\n3. API Response:")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)

except HTTPError as e:
    print(f"\n❌ HTTP Error: {e.code} - {e.reason}")
    try:
        error_body = e.read().decode('utf-8')
        print(f"   Error details: {error_body}")
    except:
        pass
except URLError as e:
    print(f"\n❌ URL Error: {e.reason}")
except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
