import requests
import json

class ChatEngine:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def get_response(self, user_input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "（原有系统提示）"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                response_data = response.json()
                return response_data["choices"][0]["message"]["content"]
            else:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Error: {response.status_code} - {error_message}")
        except Exception as e:
            raise Exception(f"请求失败: {str(e)}")
