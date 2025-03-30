# from flask import Flask, render_template, request, jsonify
# import requests
# import random
# import time
# from flask_cors import CORS
#
# app = Flask(__name__)
# CORS(app)
#
# # DeepSeek API 配置
# API_KEY = "sk-beb9e43a63e1427da3e96c5e9808f371"
# API_URL = "https://api.deepseek.com/v1/chat/completions"
#
# messages = [
#     {"role": "system", "content": "You are an AI learning coach..."}
# ]
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# @app.route('/chat', methods=['POST'])
# def chat():
#     user_input = request.json.get("message")
#     if not user_input:
#         return jsonify({"error": "Empty message"}), 400
#
#     messages.append({"role": "user", "content": user_input+",只用给我4周的计划内容"})
#
#     # 生成随机等待时间（20-50秒）
#     wait_time = round(random.uniform(20, 50), 2)
#     time.sleep(wait_time)  # 模拟处理时间
#
#     # 调用API
#     response = requests.post(API_URL,
#         json={
#             "model": "deepseek-chat",
#             "messages": messages,
#             "stream": False
#         },
#         headers={
#             "Authorization": f"Bearer {API_KEY}",
#             "Content-Type": "application/json"
#         })
#
#     if response.status_code != 200:
#         return jsonify({"error": "API request failed"}), 500
#
#     ai_reply = response.json()["choices"][0]["message"]["content"]
#     messages.append({"role": "assistant", "content": ai_reply})
#
#     return jsonify({
#         "reply": ai_reply,
#         "wait_time": wait_time  # 返回等待时间
#     })
#
# if __name__ == '__main__':
#     app.run(debug=True)






# 第二版加流式输出

from flask import Flask, render_template, request, jsonify, Response
import requests
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# DeepSeek API 配置
API_KEY = "sk-beb9e43a63e1427da3e96c5e9808f371"
API_URL = "https://api.deepseek.com/v1/chat/completions"

messages = [
    {"role": "system", "content": "You are an AI learning coach..."}
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    messages.append({"role": "user", "content": user_input + ",只用给我4周的计划内容"})

    # 调用API并开启流式
    response = requests.post(API_URL,
                             json={
                                 "model": "deepseek-chat",
                                 "messages": messages,
                                 "stream": True  # 启用流式
                             },
                             headers={
                                 "Authorization": f"Bearer {API_KEY}",
                                 "Content-Type": "application/json"
                             },
                             stream=True
                             )

    if response.status_code != 200:
        return jsonify({"error": "API request failed"}), 500

    def generate():
        full_reply = ''
        for chunk in response.iter_lines():
            # 过滤保持连接的空行
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                # 打印原始响应数据方便调试
                print("Raw chunk:", decoded_chunk)

                if decoded_chunk.startswith('data:'):
                    json_str = decoded_chunk[5:].strip()
                    try:
                        data = json.loads(json_str)
                        content = data['choices'][0]['delta'].get('content', '')
                        if content:
                            full_reply += content
                            # 流式输出到控制台
                            print(content, end='', flush=True)
                            # 发送到前端
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        pass
        # 将完整回复添加到对话历史
        messages.append({"role": "assistant", "content": full_reply})
        print("\nStream complete")

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)