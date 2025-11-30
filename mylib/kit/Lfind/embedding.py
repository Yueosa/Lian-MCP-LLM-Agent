import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("QW_EMBEDDING_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def get_embedding(input: str) -> list[float]:
    return (client.embeddings.create(
        model="text-embedding-v4",
        input=input,
        dimensions=1536,
        encoding_format="float"
    )).data[0].embedding

if __name__ == "__main__":
    print(get_embedding(input=input("输入文字: ")))
