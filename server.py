import socket
from threading import Thread
import argparse
import sys

HEAD_SIZE = 10
IP = "localhost"

parser = argparse.ArgumentParser(description="PChat Server", usage='python3 server.py [options]',
                                 epilog="Press ctrl+c to close server.")
parser.add_argument("-p", "--port", help="Port to be used by the server. Expects one argument", type=int, default=1234)
PORT = parser.parse_args().port
server_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_sckt.bind((IP, PORT))
except OSError as e:
    print("Connection error: "+str(e.strerror))
    sys.exit(0)
except Exception as e:
    print("General error: "+str(e))
    sys.exit(0)
server_sckt.listen()
clients = {}


def msg_recv(client_sckt):
    msg_header = client_sckt.recv(HEAD_SIZE)
    if not len(msg_header):
        return False
    msg_len = int(msg_header.decode("utf-8").strip())
    return {"header": msg_header, "data": client_sckt.recv(msg_len)}


def accept_clients():
    while True:
        new_client_sckt, new_client_addr = server_sckt.accept()
        init_data = msg_recv(new_client_sckt)
        if not init_data:
            continue
        username = init_data["data"].decode("utf-8")
        clients[new_client_sckt] = username
        print(f"Accepted new connection from {new_client_addr[0]}:{new_client_addr[1]} username: {username}")
        client_thread = Thread(target=handle_client, args=(new_client_sckt,))
        client_thread.start()


def handle_client(client_sckt):
    username = clients[client_sckt]
    while True:
        msg = msg_recv(client_sckt)
        if not msg or msg['data'].decode('utf-8') == "/q":
            print(f"Closed connection from {username}")
            send_all(f"{username} has left the room.")
            clients.pop(client_sckt)
            client_sckt.close()
            break
        content = msg['data'].decode('utf-8')
        print(f"Received from {username}: {content}")
        send_all(f"{username}: {content}")


def send_all(msg):
    for sckt in clients:
        sckt.send(bytes(f"{len(msg):<{HEAD_SIZE}}{msg}", "utf-8"))


try:
    thread = Thread(target=accept_clients)
    thread.setDaemon(True)
    thread.start()
    thread.join()
    server_sckt.close()
except KeyboardInterrupt:
    print("You closed the server.")
    server_sckt.close()