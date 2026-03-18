import json
from openai import OpenAI

import loguru

logger = loguru.logger


class LLM:
    def __init__(self, api_key: str, base_url: str, system_promt_path: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.system_promt_path = system_promt_path

        with open(self.system_promt_path, "r") as f:
            self.system_promt = f.read()

    def generate(self, user_msg: str):
        logger.info(f"用户消息: {user_msg}")

        messages = [
            {"role": "system", "content": self.system_promt},
            {"role": "user", "content": user_msg}
        ]

        logger.info(f"llm generate messages: {json.dumps(messages, ensure_ascii=False)}")

        api_params = {
            "model": "Qwen3-4B-Instruct-2507",
            "messages": messages,
            "stream": False,
            "extra_body": {
                "chat_template_kwargs": {"enable_thinking": True}
            },
            "temperature": 0.7,
            "max_completion_tokens": 256,
            "top_p": 1
        }

        response = self.client.chat.completions.create(**api_params)
        choice = response.choices[0]
        reasoning_content = getattr(choice.message, "reasoning_content", "")
        content = choice.message.content

        logger.info(f"推理内容: {reasoning_content}")
        logger.info(f"生成内容: {content}")

        return content

if __name__ == "__main__":
    llm = LLM(
        api_key="EMPTY",
        base_url="http://YOUR_LLM_SERVER_IP:8093/v1",
        system_promt_path="conf/system_prompt_intent.txt"
    )
    llm.generate("tell me a joke")
