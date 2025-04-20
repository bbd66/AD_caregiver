import httpx
from core.config import settings

class DeepseekService:
    def __init__(self):
        self.api_url = settings.DEEPSEEK_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }
    
    async def get_response(self, user_input: str) -> str:
        """
        调用DeepSeek API获取回复
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 提取回复内容
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "抱歉，我无法理解您的问题。"
                    
        except httpx.RequestError as e:
            raise Exception(f"请求错误: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API返回错误码 {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"发生未知错误: {str(e)}")

# 创建服务实例
deepseek_service = DeepseekService() 