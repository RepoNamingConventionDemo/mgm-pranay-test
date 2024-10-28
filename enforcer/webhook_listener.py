import os
import hmac
import hashlib
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

GITHUB_TOKEN = os.getenv('GIT_TOKEN')
ORGANIZATION_NAME = os.getenv('ORGANIZATION_NAME')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET').encode()

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify the webhook secret
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({'message': 'Invalid signature'}), 403

    data = request.json
    action = data.get('action')
    repository_name = data.get('repository', {}).get('name', '')

    if action == 'created':
        print(f"Received repository name: {repository_name}")
        if not repository_name.startswith('mgm-'):
            delete_repository(repository_name)
            return jsonify({'message': f'Repository {repository_name} deleted for not following naming convention.'}), 200
        else:
            return jsonify({'message': f'Repository {repository_name} follows naming convention.'}), 200

    return jsonify({'message': 'No action taken'}), 200

def verify_signature(data, signature):
    """Verify the webhook signature."""
    hash_signature = hmac.new(WEBHOOK_SECRET, data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f'sha256={hash_signature}', signature)

def delete_repository(repo_name):
    """Delete the repository if it doesn't follow naming convention."""
    url = f'https://api.github.com/repos/{ORGANIZATION_NAME}/{repo_name}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f'Repository {repo_name} deleted successfully.')
    else:
        print(f'Error deleting repository: {response.content}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
