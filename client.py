import socket
from threading import Thread
import tkinter
import sys
import os
from pathlib import Path

HEAD_SIZE = 10
MAIN_HEIGHT = 280
MAIN_WIDTH = 400


def die(msg):
    print(msg)
    canvas.destroy()


def real_path(rel_path):
    """
    :param rel_path: file's location relative to the main .py script.
    :return: if the program is opened as an executable, using the "MEIPASS" attribute we get the path of the resource
    bundled to it. if opened as a script, the resource is expected to reside in the same directory as the script,
    so a fitting path will be returned.
    """
    return getattr(sys, '_MEIPASS', str(Path(os.path.abspath(__file__)).parent))+"/"+rel_path


def msg_recv(sckt):
    """
    :param sckt: client socket to receive the message from server.
    :return: decomposition of the input into "header": integer representing the length, and "data": the message itself
    """
    msg_header = sckt.recv(HEAD_SIZE)
    if not len(msg_header):
        return False
    msg_len = int(msg_header.decode("utf-8").strip())
    return {"header": msg_header, "data": sckt.recv(msg_len)}


def login(event=None):
    """
    gets user input from text boxes.
    if not empty: establishes connection & destroys the log in window.
    """
    con_err["text"] = ""
    ip = ip_box.get()
    try:
        socket.inet_aton(ip)
        label_no_ip["text"] = ""
    except socket.error:
        label_no_ip["text"] = "IP address is not valid!"
    port = port_box.get()
    if port == "":
        label_no_port["text"] = "Port cannot be empty!"
    else:
        label_no_port["text"] = ""
    username = username_box.get()
    if username == "":
        label_no_username["text"] = "User name cannot be empty!"
    else:
        label_no_username["text"] = ""
    if username != "" and ip != "" and port != "":
        connect(ip, int(port), username)


def connect(ip, port, username):
    # attempt to connect to the chat room server
    try:
        client_sckt.connect((ip, port))
    except ConnectionRefusedError:
        con_err["text"] = "Can't connect to server."
        print("Can't connect to server.")
        return
    client_sckt.send(bytes(f"{len(username):<{HEAD_SIZE}}{username}", "utf-8"))
    login_canvas.destroy()
    # if successful, start thread for listening to new messages from the server:
    thread = Thread(target=listen)
    thread.setDaemon(
        True)  # closing tk window a.k.a the main thread, will shut down the program even if this thread is
    # running
    thread.start()
    inputbox["state"] = "normal"
    send_button["state"] = "normal"


def listen():
    """
    looks for new messages sent by the server, then inserts them in the messages array in the app's main window
    """
    while True:
        try:
            msg = msg_recv(client_sckt)
            if not msg:
                raise ConnectionResetError
            content = msg['data'].decode("utf-8")
            msg_arr.insert(tkinter.END, content)
            msg_arr.see(tkinter.END)  # automatically scroll to the end
        except ConnectionResetError:
            die("Connection closed.")
        except Exception as e:
            die("General error: " + str(e))


def send(evnet=None):
    try:
        msg = my_msg.get()
        client_sckt.send(bytes(f"{len(msg):<{HEAD_SIZE}}{msg}", "utf-8"))
        if msg == "/q":  # exit the chat room
            canvas.quit()
        else:
            my_msg.set("")
    except BrokenPipeError:
        die("Connection closed.")


def close_main_chat():
    my_msg.set("/q")
    send()


# main chat window configuration:
canvas = tkinter.Tk(className="PChat")
canvas.title("PChat")
canvas.geometry(f"{MAIN_WIDTH}x{MAIN_HEIGHT}+{int(canvas.winfo_screenwidth()/2-MAIN_WIDTH/2)}+"
                f"{int(canvas.winfo_screenheight()/2-MAIN_HEIGHT/2)}")
canvas.iconphoto(True, tkinter.Image("photo", file=real_path('favicon.png')))
canvas.rowconfigure(0, weight=1)
canvas.rowconfigure(1, weight=0)
canvas.columnconfigure(0, weight=1)
canvas.columnconfigure(1, weight=0)
canvas.protocol("WM_DELETE_WINDOW", close_main_chat)

msgs_frame = tkinter.Frame(canvas)  # where the messages will appear
my_msg = tkinter.StringVar()
scrollbar = tkinter.Scrollbar(msgs_frame)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_arr = tkinter.Listbox(msgs_frame, yscrollcommand=scrollbar.set)
msg_arr.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
scrollbar.config(command=msg_arr.yview)
msgs_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")


# text box and a button for receiving user input.
# the input box & the send button are disabled as long as the user didn't successfully log in.
entry = tkinter.Frame(canvas)
inputbox = tkinter.Entry(entry, state="disabled", textvariable=my_msg)
inputbox.pack(fill=tkinter.BOTH, expand=True)
inputbox.bind("<Return>", send)
send_button = tkinter.Button(canvas, text="Send", state="disabled", command=send)
entry.grid(row=1, column=0, padx=10, sticky="ew")
send_button.grid(row=1, column=1, pady=10, sticky="ew")


# login in window configuration:
login_canvas = tkinter.Toplevel(class_="Pchat")
login_canvas.title("Pchat")
login_canvas.iconphoto(True, tkinter.Image("photo", file=real_path('favicon.png')))
login_canvas.lift()
login_canvas.attributes("-topmost", True)  # push the login window to the front
login_canvas.resizable(False, False)

ip_label = tkinter.Label(login_canvas, text="Server IP Address: ")
ip_label.grid(row=0, column=0)
ip_box = tkinter.Entry(login_canvas)
ip_box.grid(row=0, column=1)
label_no_ip = tkinter.Label(login_canvas, text="")
label_no_ip.grid(row=0, column=2)
port_label = tkinter.Label(login_canvas, text="Port: ")
port_label.grid(row=1, column=0)
port_box = tkinter.Entry(login_canvas)
port_box.grid(row=1, column=1)
label_no_port = tkinter.Label(login_canvas, text="")
label_no_port.grid(row=1, column=2)
username_label = tkinter.Label(login_canvas, text="Enter your user name: ")
username_label.grid(row=2, column=0)
username_box = tkinter.Entry(login_canvas, width=20)
username_box.grid(row=2, column=1)
username_box.bind("<Return>", login)
label_no_username = tkinter.Label(login_canvas, text="")
label_no_username.grid(row=2, column=2)
login_button = tkinter.Button(login_canvas, width=7, text="Log in", command=login)
login_button.grid(row=3, column=1)
con_err = tkinter.Label(login_canvas, text="")
con_err.grid(row=4, column=1)
login_canvas.geometry(f"+{int(login_canvas.winfo_screenwidth()/2-login_canvas.winfo_x()/2)}+"
                      f"{int(login_canvas.winfo_screenheight()/2-login_canvas.winfo_y()/2)}")


client_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# exit before log in
login_canvas.protocol("WM_DELETE_WINDOW", lambda: canvas.destroy())


try:
    tkinter.mainloop()  # main thread
except tkinter.TclError:
    print("Window was closed. Aborting connection.")
