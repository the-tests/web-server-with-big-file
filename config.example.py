TIMEOUT = 5.0
S3_BUCKET = 'bucket-name'
REGION = 'ap-northeast-1'
AWS_KEY = 'blahblah'
AWS_SECRET = 'blahblah'
ENDPOINT_URL = 'http://localhost:9000'
PORT = 7777
HOST = '0.0.0.0'
# Blocking time should be about 300~700ms for 10000 elements in chunk
# If we make chunk size too small, it will take longer to download in real time
# but blocking time will be longer
CHUNK_SIZE = 10000
