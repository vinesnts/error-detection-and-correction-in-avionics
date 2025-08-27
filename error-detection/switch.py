from math import e
import socket
import argparse
import threading


def initialize_switch(with_error, args):
    connected_es = []
    switch_port = 12345

    def receive_messages(switch_port, source_es, addr, with_error):
        while True:
            # Get data from ES
            data = source_es.recv(1024)
            
            if not data:
                source_es.close()
                break
            print("Switch %s received data from ES %s:" % (switch_port, addr[1]), data.decode())

            # Injecting error by flipping one bit
            if with_error:
                ans = list(data.decode())

                ans[5] = str(int(not int(ans[5])))
                data = ''.join(ans).encode()

            for connected in connected_es:
                destiny_es = connected[0]
                destiny_addr = connected[1]
                if destiny_addr == addr:
                    continue

                try:
                    print("Switch %s sending data to ES %s:" % (switch_port, destiny_addr[1]), data.decode())
                    destiny_es.sendto(data, destiny_addr)
                except ConnectionRefusedError:
                    print("Could not connect to destiny ES %s" % (destiny_addr[1]))
                    data = ("ES at port " + str(destiny_addr[1]) + " is not available").encode()

    switch_socket = socket.socket()
    switch_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    while True:
        try:
            switch_socket.bind(('', switch_port))
            switch_socket.listen(5)
            break
        except OSError:
            switch_port += 1

    print("Switch initiated at %s" % (switch_port))
    # put the socket into listening mode
    while True:
        # Establish connection with client.
        client, addr = switch_socket.accept()
        connected_es.append((client, addr))
        print('Switch %s got connection from %s' % (switch_port, addr))

        threading.Thread(target=receive_messages, args=(switch_port, client, addr, with_error), daemon=True).start()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--redundancy", type=int, default=1,
        help="The redundancy level (default is 1).")
    ap.add_argument("-e", "--error", type=int, default=0,
        help="Inject error on the Nth switch.")
    args = vars(ap.parse_args())

    if args["error"]:
        print(f"Switch {args['error']} with error!")
    else:
        print("Switch without error!")

    if args["redundancy"] < 1:
        print("Redundancy level must be at least 1.")
        exit(1)
    print("Redundancy level:", args["redundancy"])

    for i in range(args["redundancy"]):
        threading.Thread(target=initialize_switch, args=(args["error"] == i + 1, args), daemon=True).start()

    try:
        while True:
            ...
    except KeyboardInterrupt:
        print("\n\nShutdown...")