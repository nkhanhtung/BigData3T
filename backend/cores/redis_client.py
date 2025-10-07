import redis

r = redis.StrictRedis(
    host="localhost",  # hoặc hostname Redis nếu chạy trên server khác
    port=6379,
    db=0,
    decode_responses=True  # để giá trị đọc ra là string, không phải bytes
)
