import socket
import subprocess
import threading
import os
import fcntl
import time

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind('/tmp/tio-socket0')
sock.listen(1)

conn, addr = sock.accept()

# Start gcode-cli with stdin from socket, stderr merged to stdout
proc = subprocess.Popen(
    ['gcode-cli', '-'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT  # This merges stderr into stdout
)

# Thread to read from socket and write to gcode-cli stdin
def socket_to_stdin():
    while True:
        data = conn.recv(4096)
        if not data:
            break
        proc.stdin.write(data)
        print(f"; Received from socket:\n{data.decode().strip()}")
        proc.stdin.flush()

        time.sleep(0.2)


        # Read any immediate response from stdout
        # Set stdout to non-blocking mode
        flags = fcntl.fcntl(proc.stdout, fcntl.F_GETFL)
        fcntl.fcntl(proc.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        try:
            response = proc.stdout.read(4096)
        except BlockingIOError:
            response = b''
        if response:
            conn.sendall(response)
            print(f"; Immediate response:\n {response.decode().strip()}")
    proc.stdin.close()

# Thread to read from gcode-cli stdout (includes stderr) and write to socket
def stdout_to_socket():
    while True:
        data = proc.stdout.read(4096)
        if not data:
            break
        if data:
            print(f"; Sent to socket: {data.decode().strip()}")
        err = proc.stderr.read(4096)
        if err:
            print(f"; error from gcode-cli: {err.decode().strip()}")
        conn.sendall(data)

t1 = threading.Thread(target=socket_to_stdin)
t2 = threading.Thread(target=stdout_to_socket)

t1.start()
t2.start()

t1.join()
t2.join()

conn.close()
sock.close()