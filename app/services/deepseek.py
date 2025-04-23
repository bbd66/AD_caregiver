import httpx
from core.config import settings
import logging

class DeepseekService:
    def __init__(self):
        self.api_url = settings.DEEPSEEK_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }
    
    async def get_response(self,description: str, user_input: str) -> str:
        """
        调用DeepSeek API获取回复
        """
        try:
            logging.info("===== deepseek get_response 方法开始 =====")
            logging.info(f"输入参数: user_input={user_input}")
            logging.info(f"输入参考: description={description}")
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": description},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            logging.info(f"发送到DeepSeek API的payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                logging.info(f"DeepSeek API响应: {result}")
                
                # 提取回复内容
                if "choices" in result and len(result["choices"]) > 0:
                    reply = result["choices"][0]["message"]["content"]
                    logging.info(f"提取的回复内容: {reply}")
                    logging.info("===== deepseek get_response 方法结束 =====")
                    return reply
                else:
                    logging.error("API响应中没有找到有效的回复内容")
                    logging.info("===== deepseek get_response 方法结束 =====")
                    return "抱歉，我无法理解您的问题。"
                    
        except httpx.RequestError as e:
            logging.error(f"请求错误: {str(e)}")
            raise Exception(f"请求错误: {str(e)}")
        except httpx.HTTPStatusError as e:
            logging.error(f"API返回错误码 {e.response.status_code}: {e.response.text}")
            raise Exception(f"API返回错误码 {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logging.error(f"发生未知错误: {str(e)}")
            raise Exception(f"发生未知错误: {str(e)}")

# 创建服务实例
deepseek_service = DeepseekService() 