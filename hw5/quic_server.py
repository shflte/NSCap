import socket
import time
import struct
import threading

class Packet:
    format = "i i i i i i i i {}s".format(100) 

class QUICBase:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.send_buf = {}
        self.seq_num = {}
        self.receive_window = []
        self.receive_buffer = {}
        self.receiver_receive_buffer = {}
        self.receive_buffer_size = 10
        self.all_receive_buffer_size = 50
        self.all_receiver_receive_buffer = 10
        
        self.next_seq_num = {}
        self.base_seq_num = {}
        self.sent_time = {}
        self.acked = {}

        self.window_size = 5
        self.max_window_size = 5
        self.timeout = 1.0

        self.send_ack = 1

    def send(self, stream_id: int, data: bytes):
        """add data to the send buffer with a unique sequence number"""
        if stream_id not in self.seq_num:
            self.seq_num[stream_id] = 0
        seq_num = self.seq_num[stream_id]

        max_packet_size = 5
        for i in range(0, len(data), max_packet_size):
            packet_data = data[i:i+max_packet_size]
            finish = 0
            if i+max_packet_size >= len(data):
                finish = 1
            
            if stream_id not in self.receive_buffer:
                self.receive_buffer[stream_id] = []

            buf_size = self.receive_buffer_size - len(self.receive_buffer[stream_id])
            if buf_size <= 0:
                buf_size = 0

            all_buf_size = self.all_receive_buffer_size - sum(len(v) for v in self.receive_buffer.values())
            if all_buf_size <= 0:
                all_buf_size = 0

            message = struct.pack(Packet.format, 0, 0, finish, buf_size, all_buf_size, seq_num, seq_num, stream_id, packet_data)
            self.sent_time.setdefault(stream_id, {})[seq_num] = time.time()
            self.acked.setdefault(stream_id, {})[seq_num] = 0
            self.send_buf.setdefault(stream_id, {})[seq_num] = message

            seq_num += 1
        self.seq_num[stream_id] = seq_num

    def recv(self) -> tuple[int, bytes]:
        """Receive data from client"""
        stream_id = 0
        payload = ""
        while True:
            having_recv = 0
            receive_buffer_keys = list(self.receive_buffer.keys())
            for stream in receive_buffer_keys:
                if len(self.receive_buffer[stream]) > 0:
                    finish_flag_exist = 0
                    for packet in self.receive_buffer[stream]:
                        ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, packet)
                        if finish_flag == 1:
                            finish_flag_exist = 1
                            break
                    
                    if finish_flag_exist == 1:
                        content = []
                        for packet in self.receive_buffer[stream]:
                            ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, packet)
                            content.append([seq_num, payload.decode()])
                        content.sort()
                        is_finish = all(content[i][0] == content[i-1][0] + 1 for i in range(1, len(content)))
                        if is_finish:
                            result = ''.join([item[1] for item in content])
                            self.receive_buffer[stream].clear()
                            print(result)
                            having_recv = 1
                            break

            if having_recv == 1:
                break

        return stream_id, payload.decode()
    
    def move_base(self):
        while True:
            send_buf_keys = list(self.send_buf.keys())
            for stream in send_buf_keys:
                if stream not in self.base_seq_num:
                    break
                if stream not in self.base_seq_num:
                    break
                base = self.base_seq_num[stream]

                while stream in self.acked and base in self.acked[stream] and self.acked[stream][base] == 1:
                    self.base_seq_num[stream] += 1
                    base = self.base_seq_num[stream]
    
    def close(self):
        """Close the connection and socket"""
        self.socket.close()

class QUICServer(QUICBase):
    def __init__(self):
        super().__init__()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_addr = ""
        
        t_send_loop = threading.Thread(target=self.send_loop)
        t_send_loop.daemon = True
        t_send_loop.start()

        t_recv_loop = threading.Thread(target=self.recv_loop)
        t_recv_loop.daemon = True
        t_recv_loop.start()

        t_move_base = threading.Thread(target=self.move_base)
        t_move_base.daemon = True
        t_move_base.start()

        t_check_timeout = threading.Thread(target=self.check_timeout)
        t_check_timeout.daemon = True
        t_check_timeout.start()
    
    def listen(self, socket_addr: tuple[str, int]):
        """listen on a specific address"""
        print("listening...")
        self.socket.bind(socket_addr)
    
    def accept(self):
        """wait for incoming connection"""
        _ , _ = self.recv()

    def send_loop(self):
        """send data from the send buffer with sliding window and retransmit"""
        

        while True:
            # send data in the sliding window
            send_buf_keys = list(self.send_buf.keys())
            for stream in send_buf_keys:
                if stream not in self.next_seq_num:
                    self.next_seq_num[stream] = 0
                if stream not in self.base_seq_num:
                    self.base_seq_num[stream] = 0
                
                seq_to_send = self.next_seq_num[stream]
                if seq_to_send <= self.base_seq_num[stream] + self.window_size - 1 and seq_to_send in self.send_buf[stream] and ( stream not in self.receiver_receive_buffer or (stream in self.receiver_receive_buffer and self.receiver_receive_buffer[stream] > 0 )) and self.all_receiver_receive_buffer > 0:
                    self.socket.sendto(self.send_buf[stream][seq_to_send], self.client_addr)
                    ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, self.send_buf[stream][seq_to_send])
                    print("send --- ACK:", ACK, "SYN:", SYN, "finish_flag:", finish_flag, "receive_buffer", receive_buffer, "all_receive_buffer", all_receive_buffer, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", payload.decode())
                    self.next_seq_num[stream] += 1

    def recv_loop(self):
        while True:
            message, client_addr = self.socket.recvfrom(1024)
            self.client_addr = client_addr
            ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, message)
            print("recv --- ACK:", ACK, "SYN:", SYN, "finish_flag:", finish_flag, "receive_buffer", receive_buffer, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", payload.decode())
            if ACK == 0:
                if stream_id in self.receive_buffer:
                    if len(self.receive_buffer[stream_id]) <= self.receive_buffer_size:
                        self.receive_buffer[stream_id].append(message)
                else:
                    self.receive_buffer[stream_id] = [message]
            self.receiver_receive_buffer[stream_id] = receive_buffer
            self.all_receiver_receive_buffer = all_receive_buffer
            if ACK == 1 and SYN != 1:
                if stream_id in self.acked:
                    self.acked[stream_id][seq_num] = 1
                if self.window_size <= self.max_window_size:
                    self.window_size = self.window_size + 1
            
            buf_size = self.receive_buffer_size - len(self.receive_buffer[stream_id])
            if buf_size <= 0:
                buf_size = 0
            
            all_buf_size = self.all_receive_buffer_size - sum(len(v) for v in self.receive_buffer.values())
            if all_buf_size <= 0:
                all_buf_size = 0

            if SYN == 1:
                print("client request to connect")
                # Perform QUIC handshake

                data = (1, 1, 1, buf_size, all_buf_size, 0, 0, 0,"".encode())
                packed_data = struct.pack(Packet.format, *data)
                self.socket.sendto(packed_data, self.client_addr)
                # print("send --- ACK:", 1, "SYN:", 1, "finish_flag:", 1, "receive_buffer", buf_size, "all_receive_buffer", all_buf_size, "seq_num:", 0, "ack_num:", 0, "stream_id:", 0, "payload:", "")
                continue

            if ACK == 0 and self.send_ack == 1:
                data = (1, 0, 1, buf_size, all_buf_size, seq_num, ack_num, stream_id,"".encode())
                packed_data = struct.pack(Packet.format, *data)
                self.socket.sendto(packed_data, self.client_addr)
                # print("send --- ACK:", 1, "SYN:", 0, "finish_flag:", 1, "receive_buffer", buf_size, "all_receive_buffer", all_buf_size, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", "")
    
    def check_timeout(self):
        while True:
            acked_keys = list(self.acked.keys())
            for stream in acked_keys:
                acked_seq_keys = list(sorted(self.acked[stream].keys()))
                for seq in acked_seq_keys:
                    if stream in self.base_seq_num and seq >= self.base_seq_num[stream]:
                        now = time.time()
                        if now - self.sent_time[stream][seq] > self.timeout and self.acked[stream][seq] == 0 and ( stream not in self.receiver_receive_buffer or (stream in self.receiver_receive_buffer and self.receiver_receive_buffer[stream] > 0 )) and self.all_receiver_receive_buffer > 0:
                            self.sent_time[stream][seq] = time.time()

                            message = self.send_buf[stream][seq]

                            if stream not in self.receive_buffer:
                                self.receive_buffer[stream] = []
                            buf_size = self.receive_buffer_size - len(self.receive_buffer[stream])
                            if buf_size <= 0:
                                buf_size = 0
                            all_buf_size = self.all_receive_buffer_size - sum(len(v) for v in self.receive_buffer.values())
                            if all_buf_size <= 0:
                                all_buf_size = 0
                            
                            ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, message)
                            message = struct.pack(Packet.format, 0, 0, finish_flag, buf_size, all_buf_size, seq_num, ack_num, stream_id, payload)
                            

                            self.sent_time.setdefault(stream, {})[seq] = time.time()
                            self.acked.setdefault(stream, {})[seq] = 0
                            self.socket.sendto(message, self.client_addr)

                            if self.window_size > 1:
                                self.window_size = self.window_size - 1
                            
                            

                            print("resendresend --- ACK:", 0, "SYN:", 0, "finish_flag:", finish_flag, "receive_buffer", buf_size, "all_receive_buffer", all_buf_size, "seq_num:", seq, "ack_num:", seq, "stream_id:", stream, "payload:", payload.decode())

# server side
if __name__ == "__main__":
    server = QUICServer()
    server.listen(("", 30000))
    server.accept()

    stream = 0
    while True:
        message = "This is stream " + str(stream) + " This is stream " + str(stream)
        server.send(stream, message.encode("utf-8"))
        stream = stream + 1
        time.sleep(1)
