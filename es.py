import socket
import argparse
import threading
from encoder_decoder import EncoderDecoder


def run_client(args):
    switches = []
    last_messages = {}
    last_messages_lock = threading.Lock()   # <--- create lock
    encoder_decoder = EncoderDecoder()

    def receive_messages(algorithm, decoder, switch_socket, switch_port):
        while True:
            try:
                data = switch_socket.recv(1024)
                if not data:
                    print("\nConnection to switch at %s lost." % (switch_port))
                    with last_messages_lock:   # protect modification
                        switches.remove((switch_socket, switch_port))
                        last_messages.pop(switch_port, None)
                    break

                print("\nEncoded binary data received:", data.decode())

                with last_messages_lock:   # protect reads and writes
                    if any(last_messages.values()):
                        print("Redundant message received, ignoring and cleaning...")
                        for sp in last_messages:
                            last_messages[sp] = None
                        continue

                error = False
                if algorithm == 'parity':
                    error = not decoder.decode_data_parity(data)
                elif algorithm == 'crc':
                    error = decoder.decode_data_crc(data)
                elif algorithm == 'hamming':
                    error = decoder.decode_data_hamming(data)

                with last_messages_lock:
                    if not error:
                        last_messages[switch_port] = data.decode()
                        print("Message: %s" % (data.decode(), ))

                        if all(v is not None for v in last_messages.values()):
                            print("All messages received, cleaning...")
                            for sp in last_messages:
                                last_messages[sp] = None
                    else:
                        last_messages[switch_port] = False
                        print("Error detected in the received message.")

            except Exception as e:
                print(f"Error in receive thread for port {switch_port}: {e}")
                break

    # --- Setup connections ---
    for switch_port in args["ports"]:
        try:
            switch_socket = socket.socket()
            switch_socket.connect(('127.0.0.1', switch_port))
            print("Connected to switch at %s" % (switch_port))
            switches.append((switch_socket, switch_port))
            with last_messages_lock:
                last_messages[switch_port] = None

            threading.Thread(
                target=receive_messages,
                args=(args['algorithm'], encoder_decoder, switch_socket, switch_port),
                daemon=True
            ).start()
        except ConnectionRefusedError:
            print("Could not connect to switch at %s" % (switch_port))
            break

    # --- Sending loop ---
    try:
        while True:
            if not switches:
                break

            msg = input("Type message to send (or 'exit' to quit): ")
            if msg.lower() == 'exit':
                break
            data = encoder_decoder.encode_binary_string(msg)
            ans = None
            if args["algorithm"] == 'parity':
                ans = encoder_decoder.encode_data_parity(data[0])
            elif args["algorithm"] == 'crc':
                ans = ''.join(encoder_decoder.encode_data_crc(bit) for bit in data)
            elif args["algorithm"] == 'hamming':
                ans = ''.join(encoder_decoder.encode_data_hamming(bit) for bit in data)

            if not ans:
                print("Error encoding data.")
                continue

            for switch_socket, _ in switches:
                switch_socket.send(ans.encode())
    except BrokenPipeError:
        print("Connection to server lost.")
    except KeyboardInterrupt:
        print("\nES shutdown...")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--algorithm", required=True, type=str,
        help="The algorithm to detect or correct error (types supported: parity, crc, hamming, reed).")
    ap.add_argument("-p", "--ports", nargs='+', type=int, required=True,
        help="List of ports for the switches to connect to.")
    args = vars(ap.parse_args())

    run_client(args)
