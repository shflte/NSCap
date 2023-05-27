import time
import struct
import threading
from quic_server import QUICBase, Packet

class QUICClient(QUICBase):
    def __init__(self):
        super().__init__()
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
        
    def connect(self, socket_addr: tuple[str, int]):
        """connect to the specific server"""
        self.socket.connect(socket_addr)
        # self.receive_buffer[0] = self.receive_buffer_size
        
        # Perform QUIC handshake
        data = (0, 1, 1, self.receive_buffer_size, self.receive_buffer_size, 0, 0, 0,"".encode())
        packed_data = struct.pack(Packet.format, *data)
        self.socket.send(packed_data)

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
                    # message = struct.pack(Packet.format, 0, 0, 0, 0, seq_to_send, seq_to_send, stream, self.send_buf[stream][seq_to_send])
                    # self.sent_time.setdefault(stream, {})[seq_to_send] = time.time()
                    # self.acked.setdefault(stream, {})[seq_to_send] = 0
                    self.socket.send(self.send_buf[stream][seq_to_send])
                    ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, self.send_buf[stream][seq_to_send])
                    print("send --- ACK:", ACK, "SYN:", SYN, "finish_flag:", finish_flag, "receive_buffer", receive_buffer, "all_receive_buffer", all_receive_buffer, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", payload.decode())
                    # print("send:", self.send_buf[stream][seq_to_send].decode())
                    self.next_seq_num[stream] += 1

    def recv_loop(self):
        while True:
            message = self.socket.recv(1024)
            ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, message)
            # print("recv --- ACK:", ACK, "SYN:", SYN, "finish_flag:", finish_flag, "receive_buffer", receive_buffer, "all_receive_buffer", all_receive_buffer, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", payload.decode())

            if ACK == 0:
                if stream_id in self.receive_buffer:
                    if len(self.receive_buffer[stream_id]) <= self.receive_buffer_size:
                        ACK, SYN, finish_flag, receive_buffer, all_receive_buffer, seq_num, ack_num, stream_id, payload = struct.unpack(Packet.format, message)
                        self.receive_buffer[stream_id].append(message)
                        # print("recv --- ACK:", ACK, "SYN:", SYN, "finish_flag:", finish_flag, "receive_buffer", receive_buffer, "all_receive_buffer", all_receive_buffer, "seq_num:", seq_num, "ack_num:", ack_num, "stream_id:", stream_id, "payload:", payload.decode())

                else:
                    self.receive_buffer[stream_id] = [message]

            self.receiver_receive_buffer[stream_id] = receive_buffer
            self.all_receiver_receive_buffer = all_receive_buffer
            if ACK == 1 and SYN != 1:
                if stream_id in self.acked:
                    self.acked[stream_id][seq_num] = 1
                if self.window_size <= self.max_window_size:
                    self.window_size = self.window_size + 1
            
            if SYN == 1 and ACK == 1:
                print("success to connect server")  

            buf_size = self.receive_buffer_size
            if stream_id in self.receive_buffer:
                buf_size = self.receive_buffer_size - len(self.receive_buffer[stream_id])
                if buf_size <= 0:
                    buf_size = 0
            
            all_buf_size = self.all_receive_buffer_size - sum(len(v) for v in self.receive_buffer.values())
            if all_buf_size <= 0:
                all_buf_size = 0
            
            if ACK == 0 and self.send_ack == 1:
                data = (1, 0, 1, buf_size, all_buf_size, seq_num, ack_num, stream_id,"".encode())
                packed_data = struct.pack(Packet.format, *data)
                self.socket.send(packed_data)
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
                            self.socket.send(message)

                            if self.window_size > 1:
                                self.window_size = self.window_size - 1

                            print("resendresend --- ACK:", 0, "SYN:", 0, "finish_flag:", finish_flag, "receive_buffer", buf_size, "all_receive_buffer", all_buf_size, "seq_num:", seq, "ack_num:", seq, "stream_id:", stream, "payload:", payload.decode())

# client side
if __name__ == "__main__":
    client = QUICClient()
    client.connect(("127.0.0.1", 30000))

    while True:
        recv_id, recv_data = client.recv()