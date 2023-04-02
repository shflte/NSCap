from setting import Setting
import random

# state: idle, sending, waiting (to resend)

# chars: 
#    idle: '.'
#   start: '<'
# sending: '-'
#     end: '>'
#    stop: '|'

class Host():
    def __init__(self, history="", packet_gentime=list(), state="idle", packetNo=0):
        self.history = history
        self.packet_gentime = packet_gentime
        # state: idle, sending, waiting (to resend), detect (collision)
        self.state = state
        # which packet this host is going to send / sending
        self.packetNo = packetNo
        # How long has the packet being sent
        self.flyingTime = 0
        # resend timer
        self.resendTimer = 0
    def sending(self, t: int) -> bool:
        if t < len(self.history):
            return self.history[t] in ['<', '-', '>', '|', '?']
        else:
            return self.state == "sending"

def show_hosts_history(hosts: list[Host], setting: Setting):
    for i in range(len(hosts)):
        genTimeString = [" "] * setting.total_time
        for time in hosts[i].packet_gentime:
            genTimeString[time - 1] = 'V'
        genTimeString = "    " + "".join(genTimeString)
        print(genTimeString)
        print(f'h{i}: {hosts[i].history}')

def aloha(setting: Setting, show_history=True):
    packets = setting.gen_packets()
    print(packets)
    hosts = [Host("", packets[i], "idle", 0) for i in range(setting.host_num)]
    successTime = 0
    idleTime = 0

    # detect if host collide with others
    def collision(host: Host, end: int) -> bool:
        start = end - setting.packet_time if end - setting.packet_time >= 0 else 0
        for t in range(start, end + 1):
            for otherhost in hosts:
                if otherhost != host and otherhost.sending(t):
                    return True
        return False

    for t in range(setting.total_time):
        for host in hosts:
            if host.state == "idle":
                if host.packetNo < len(host.packet_gentime) and t + 1 >= host.packet_gentime[host.packetNo]:
                    # start sending
                    host.state = "sending"
                    host.flyingTime = 1

                    host.history += "<"
                else:
                    # remain idling
                    host.history += "."
            elif host.state == "sending":
                if host.flyingTime + 1 == setting.packet_time:
                    host.history += "?"
                else:
                    host.flyingTime += 1
                    host.history += "-"
                    
            elif host.state == "waiting":
                host.resendTimer -= 1
                host.history += "."
                # resume sending
                if not host.resendTimer:
                    host.state = "idle"

        for host in hosts:
            if host.state == "sending" and host.history[t] == '?':
                # detect collision
                if collision(host, t):
                    # random.seed(setting.seed)
                    host.resendTimer = random.randint(1, setting.max_colision_wait_time)
                    host.state = "waiting"
                    host.history = host.history[:-1] + "|"
                # success transmit
                else:
                    host.state = "idle"
                    host.history = host.history[:-1] + ">"
                    successTime += 1
                    host.packetNo += 1 if host.packetNo < len(host.packet_gentime) else 0

        allIdle = True
        for host in hosts:
            if host.history[t] != '.':
                allIdle = False
                break
        if allIdle:
            idleTime += 1

    if show_history:
        show_hosts_history(hosts, setting)

    success_rate = round(successTime * setting.packet_time / setting.total_time, 2)
    idle_rate = round(idleTime / setting.total_time, 2)
    collision_rate = round(1 - success_rate - idle_rate, 2)
    return success_rate, idle_rate, collision_rate

def slotted_aloha(setting: Setting, show_history=True):
    packets = setting.gen_packets()
    print(packets)
    hosts = [Host("", packets[i], "idle", 0) for i in range(setting.host_num)]
    successTime = 0
    idleTime = 0

    # detect if host collide with others
    def collision(host: Host, end: int) -> bool:
        start = end - setting.packet_time + 1 if end - setting.packet_time >= 0 else 0
        for t in range(start, end + 1):
            for otherhost in hosts:
                if otherhost != host and otherhost.sending(t):
                    return True
        return False
    
    def begin(t: int) -> bool:
        return not (t % setting.packet_time)
    
    def resend() -> bool:
        # random.seed(setting.seed)
        return random.random() <= setting.p_resend

    for t in range(setting.total_time):
        for host in hosts:
            if host.state == "idle":
                if begin(t) and host.packetNo < len(host.packet_gentime) and t + 1 >= host.packet_gentime[host.packetNo]:
                    # start sending
                    host.state = "sending"
                    host.flyingTime = 1
                    host.history += "<"
                else:
                    # remain idling
                    host.history += "."

            elif host.state == "sending":
                if host.flyingTime + 1 == setting.packet_time:
                    host.history += "?"
                else:
                    host.flyingTime += 1
                    host.history += "-"

            elif host.state == "waiting":
                if begin(t) and resend():
                    host.state = "sending"
                    host.flyingTime = 1
                    host.history += "<"
                else: 
                    host.history += "."
                # resume sending

        allIdle = True
        for host in hosts:
            if host.history[t] != '.':
                allIdle = False
                break
        if allIdle:
            idleTime += 1
    
        for host in hosts:
            if host.state == "sending" and host.history[t] == '?':
                # detect collision
                if collision(host, t):
                    # random.seed(setting.seed)
                    host.resendTimer = random.randint(1, setting.max_colision_wait_time)
                    host.state = "waiting"
                    host.history = host.history[:-1] + "|"
                # success transmit
                else:
                    host.state = "idle"
                    host.history = host.history[:-1] + ">"
                    successTime += 1
                    host.packetNo += 1 if host.packetNo < len(host.packet_gentime) else 0

    if show_history:
        show_hosts_history(hosts, setting)

    success_rate = round(successTime * setting.packet_time / setting.total_time, 2)
    idle_rate = round(idleTime / setting.total_time, 2)
    collision_rate = round(1 - success_rate - idle_rate, 2)
    return success_rate, idle_rate, collision_rate

def csma(setting: Setting, show_history=True):
    packets = setting.gen_packets()
    print(packets)
    hosts = [Host("", packets[i], "idle", 0) for i in range(setting.host_num)]
    successTime = 0
    idleTime = 0

    def maySend(host: Host, t: int) -> bool:
        for otherhost in hosts:
            if otherhost != host and t - setting.link_delay > 0 and otherhost.sending(t - setting.link_delay):
                return False
        return True

    # detect if host collide with others
    def collision(host: Host, end: int) -> bool:
        start = end - setting.packet_time if end - setting.packet_time >= 0 else 0
        for t in range(start, end + 1):
            for otherhost in hosts:
                if otherhost != host and otherhost.sending(t):
                    return True
        return False

    for t in range(setting.total_time):
        for host in hosts:
            if host.state == "idle":
                if maySend(host, t) and host.packetNo < len(host.packet_gentime) and t + 1 >= host.packet_gentime[host.packetNo]:
                    # start sending
                    host.state = "sending"
                    host.flyingTime = 1

                    host.history += "<"
                else:
                    # remain idling
                    host.history += "."
            elif host.state == "sending":
                if host.flyingTime + 1 == setting.packet_time:
                    host.history += "?"
                else:
                    host.flyingTime += 1
                    host.history += "-"
                    
            elif host.state == "waiting":
                host.resendTimer -= 1
                host.history += "."
                # resume sending
                if not host.resendTimer:
                    host.state = "idle"

        for host in hosts:
            if host.state == "sending" and host.history[t] == '?':
                # detect collision
                if collision(host, t):
                    # random.seed(setting.seed)
                    host.resendTimer = random.randint(1, setting.max_colision_wait_time)
                    host.state = "waiting"
                    host.history = host.history[:-1] + "|"
                # success transmit
                else:
                    host.state = "idle"
                    host.history = host.history[:-1] + ">"
                    successTime += 1
                    host.packetNo += 1 if host.packetNo < len(host.packet_gentime) else 0

        allIdle = True
        for host in hosts:
            if host.history[t] != '.':
                allIdle = False
                break
        if allIdle:
            idleTime += 1

    if show_history:
        show_hosts_history(hosts, setting)

    success_rate = round(successTime * setting.packet_time / setting.total_time, 2)
    idle_rate = round(idleTime / setting.total_time, 2)
    collision_rate = round(1 - success_rate - idle_rate, 2)
    return success_rate, idle_rate, collision_rate

def csma_cd(setting: Setting, show_history=True):
    packets = setting.gen_packets()
    print(packets)
    hosts = [Host("", packets[i], "idle", 0) for i in range(setting.host_num)]
    successTime = 0
    idleTime = 0

    def maySend(host: Host, t: int) -> bool:
        for otherhost in hosts:
            if otherhost != host and t > 0 and otherhost.sending(t - setting.link_delay):
                return False
        return True

    # detect if host collide with others "after" transmission
    def collision(host: Host, end: int) -> bool:
        start = end - setting.packet_time if end - setting.packet_time >= 0 else 0
        for t in range(start, end + 1):
            for otherhost in hosts:
                if otherhost != host and otherhost.sending(t):
                    return True
        return False
    
    # detect if host collide with others "during" transmission
    def colliding(host: Host, t: int) -> bool:
        for otherhost in hosts:
            if otherhost != host and otherhost.sending(t - 1 - setting.link_delay):
                return True
        return False

    for t in range(setting.total_time):
        for host in hosts:
            if host.state == "idle":
                if maySend(host, t) and host.packetNo < len(host.packet_gentime) and t + 1 >= host.packet_gentime[host.packetNo]:
                    # start sending
                    host.state = "sending"
                    host.flyingTime = 1

                    host.history += "<"
                else:
                    # remain idling
                    host.history += "."
            elif host.state == "sending":
                if host.flyingTime + 1 == setting.packet_time:
                    host.history += "?"
                else:
                    if colliding(host, t):
                        # random.seed(setting.seed)
                        host.resendTimer = random.randint(1, setting.max_colision_wait_time)
                        host.state = "waiting"
                        host.history += "|"
                    else:
                        host.flyingTime += 1
                        host.history += "-"
                    
            elif host.state == "waiting":
                host.resendTimer -= 1
                host.history += "."
                # resume sending
                if not host.resendTimer:
                    host.state = "idle"

        for host in hosts:
            if host.state == "sending" and host.history[t] == '?':
                # detect collision
                if collision(host, t):
                    # random.seed(setting.seed)
                    host.resendTimer = random.randint(1, setting.max_colision_wait_time)
                    host.state = "waiting"
                    host.history = host.history[:-1] + "|"
                # success transmit
                else:
                    host.state = "idle"
                    host.history = host.history[:-1] + ">"
                    successTime += 1
                    host.packetNo += 1 if host.packetNo < len(host.packet_gentime) else 0

        allIdle = True
        for host in hosts:
            if host.history[t] != '.':
                allIdle = False
                break
        if allIdle:
            idleTime += 1

    if show_history:
        show_hosts_history(hosts, setting)

    success_rate = round(successTime * setting.packet_time / setting.total_time, 2)
    idle_rate = round(idleTime / setting.total_time, 2)
    collision_rate = round(1 - success_rate - idle_rate, 2)
    return success_rate, idle_rate, collision_rate
