import base64
import time
import hmac
import hashlib


def generate_signature(
    e: str,
    t: str,
) -> dict:
    """
    根据输入参数 e 和 t 生成签名和时间戳。

    Args:
        e: 第一个输入参数。
        t: 第二个输入参数。

    Returns:
        一个包含 'signature' 和 'timestamp' 的字典。
    """
    # 1. 获取当前时间的毫秒级时间戳
    timestamp_ms = int(time.time() * 1000)
    # timestamp_ms = 1760369828098

    encoded_t = t.encode("utf-8")
    b64_encoded_t = base64.b64encode(encoded_t).decode("utf-8")

    # 2. 拼接字符串
    message_string = f"{e}|{b64_encoded_t}|{timestamp_ms}"

    # 3. 计算 n
    n = timestamp_ms // (5 * 60 * 1000)

    # 4. 计算中间密钥 o (HMAC-SHA256)
    key1 = "junjie".encode("utf-8")
    msg1 = str(n).encode("utf-8")
    intermediate_key = hmac.new(key1, msg1, hashlib.sha256).hexdigest()

    # 5. 计算最终签名 (HMAC-SHA256)
    key2 = intermediate_key.encode("utf-8")
    msg2 = message_string.encode("utf-8")
    final_signature = hmac.new(key2, msg2, hashlib.sha256).hexdigest()

    # 6. 返回结果
    return {"signature": final_signature, "timestamp": timestamp_ms}


if __name__ == "__main__":
    # 示例用法
    e_value = "requestId,f0bf7b75-09f4-40db-a5c2-7f3749d46d62,timestamp,1760369828098,user_id,21ea9ec3-e492-4dbb-b522-fc0eaf64f0f6"
    t_value = "hi"
    result = generate_signature(e_value, t_value)
    print(f"生成的签名: {result['signature']}")
    print(f"时间戳: {result['timestamp']}")
