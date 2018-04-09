# -*- coding:UTF-8 -*-
import base64
import hashlib
import socket

# 将请求头分离出来，格式化
def get_headers(data):
    """
    将请求头格式化成字典
    :param data:
    :return:
    """
    header_dict = {}
    data = str(data, encoding='utf-8')

    for i in data.split('\r\n'):
        print(i)
    header, body = data.split('\r\n\r\n', 1)
    header_list = header.split('\r\n')
    for i in range(0, len(header_list)):
        if i == 0:
            if len(header_list[i].split(' ')) == 3:
                header_dict['method'], header_dict['url'], header_dict['protocol'] = header_list[i].split(' ')
        else:
            k, v = header_list[i].split(':', 1)
            header_dict[k] = v.strip()
    return header_dict

def send_msg(conn, msg_bytes):
    """
    WebSocket服务端向客户端发送消息
    :param conn: 客户端连接到服务器端的socket对象,即： conn,address = socket.accept()
    :param msg_bytes: 向客户端发送的字节
    :return:
    """
    import struct

    token = b"\x81"
    length = len(msg_bytes)
    if length < 126:
        token += struct.pack("B", length)
    elif length <= 0xFFFF:
        token += struct.pack("!BH", 126, length)
    else:
        token += struct.pack("!BQ", 127, length)

    msg = token + msg_bytes
    conn.send(msg)
    return True


sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# 注意参数是一个元组
sock.bind(('127.0.0.1',8002))
sock.listen(5)

# 等待用户连接
conn,address = sock.accept()
# 握手消息
data = conn.recv(8096)
print(data)
# 提取请求头信息
headers = get_headers(data)
print(headers)

# 获取握手消息之后，magic string,sha1加密
# 对请求头中的sec-websocket-key进行加密
response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
      "Upgrade:websocket\r\n" \
      "Connection: Upgrade\r\n" \
      "Sec-WebSocket-Accept: %s\r\n" \
      "WebSocket-Location: ws://%s%s\r\n\r\n"  # 这一行有没有都可以，这里有两个换行是因为请求头和请求体都是用两个空行分割开的
# 固定的值
magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
# 获取到客户端生成的字符串，和magic_string结合进行加密
value = headers['Sec-WebSocket-Key'] + magic_string
# websocket 协议规定的加密方式
ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])
# 响应【握手】信息发送给客户端，转成二进制
conn.send(bytes(response_str, encoding='utf-8'))
#接收的数据都是字节

while True:
    info = conn.recv(8096)
    # 客户端发送的东西不能直接拿到，都需要进行位运算，有一个规则，第几位代表什么
    # print(info)
    payload_len = info[1] & 127
    if payload_len == 126:
        extend_payload_len = info[2:4]
        mask = info[4:8]
        decoded = info[8:]
    elif payload_len == 127:
        extend_payload_len = info[2:10]
        mask = info[10:14]
        decoded = info[14:]
    else:
        extend_payload_len = None
        mask = info[2:6]
        decoded = info[6:]

    bytes_list = bytearray()
    for i in range(len(decoded)):
        chunk = decoded[i] ^ mask[i % 4]
        bytes_list.append(chunk)
    body = str(bytes_list, encoding='utf-8')
    # body = str(bytes_list, encoding='gbk')
    print(body)

    body = body+'付佳诚是猪'
    send_msg(conn,bytes(body,encoding='utf-8'))












