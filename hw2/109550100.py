from setting import get_hosts, get_switches, get_links, get_ip, get_mac

class packet:
    def __init__(self, srcIp, dstIp, srcMac, dstMac, payload):
        self.srcIp = srcIp
        self.dstIp = dstIp
        self.srcMac = srcMac
        self.dstMac = dstMac
        self.payload = payload

class host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac 
        self.port_to = None 
        self.arp_table = dict() # maps IP addresses to MAC addresses

    def add(self, node):
        self.port_to = node

    def show_table(self):
        print(f'---------------{self.name}:')
        for key, value in self.arp_table.items():
            print(f'{key} : {value}')

    def clear(self):
        self.arp_table.clear()

    def update_arp(self, ip, mac):
        self.arp_table[ip] = mac

    def handle_packet(self, recvpkt: packet): # handle incoming packets
        if recvpkt.dstMac == self.mac or (recvpkt.dstMac == "ffff" and recvpkt.dstIp == self.ip):
            if recvpkt.dstIp not in self.arp_table:
                self.update_arp(recvpkt.srcIp, recvpkt.srcMac)

            if recvpkt.payload == "icmp_req":
                sendpkt = packet(self.ip, recvpkt.srcIp, self.mac, recvpkt.srcMac, "icmp_res")
                self.send(sendpkt)
            elif recvpkt.payload == "arp_req":
                sendpkt = packet(self.ip, recvpkt.srcIp, self.mac, recvpkt.srcMac, "arp_res")
                self.send(sendpkt)
            else: # do nothing while recving respond message
                pass

    def ping(self, dstIp): # handle a ping request
        if dstIp not in self.arp_table.keys():
            sendpkt = packet(self.ip, dstIp, self.mac, "ffff", "arp_req")
            self.send(sendpkt)
        sendpkt = packet(self.ip, dstIp, self.mac, self.arp_table[dstIp], "icmp_req")
        self.send(sendpkt)
        
    def send(self, pkt: packet):
        node = self.port_to # get node connected to this host
        if isinstance(node, host) and node.ip == pkt.dstIp:
            node.update_arp(pkt.srcIp, pkt.srcMac)
        elif isinstance(node, switch):
            node.update_mac(pkt.srcMac, node.adj_node[self.name])
        node.handle_packet(pkt) # send packet to the connected node

class switch:
    def __init__(self, name):
        self.name = name
        self.mac_table = dict() # maps MAC addresses to port numbers
        self.port_to = list() 
        self.adj_node = dict() # maps hostname to port

    def add(self, node): # link with other hosts or switches
        self.adj_node[node.name] = len(self.port_to)
        self.port_to.append(node)

    def show_table(self):
        print(f'---------------{self.name}:')
        for key, value in self.mac_table.items():
            print(f'{key} : {value}')

    def clear(self):
        self.mac_table.clear()

    def update_mac(self, mac, port):
        self.mac_table[mac] = port

    def handle_packet(self, recvpkt: packet): # handle incoming packets
        recvport = self.mac_table[recvpkt.srcMac]
        if recvpkt.dstMac == "ffff" or recvpkt.dstMac not in self.mac_table.keys(): # broadcast or flooding
            for i in range(len(self.port_to)):
                if i == recvport:
                    continue
                self.send(i, recvpkt)
        else:
            self.send(self.mac_table[recvpkt.dstMac], recvpkt)

    def send(self, idx, pkt: packet): # send to the specified port
        node = self.port_to[idx]
        if isinstance(node, host) and node.ip == pkt.dstIp:
            node.update_arp(pkt.srcIp, pkt.srcMac)
        elif isinstance(node, switch):
            node.update_mac(pkt.srcMac, node.adj_node[self.name])
        node.handle_packet(pkt) 

def add_link(tmp1, tmp2): # create a link between two nodes
    if tmp1 in host_dict.keys() and tmp2 in host_dict.keys():
        host_dict[tmp1].add(host_dict[tmp2])
        host_dict[tmp2].add(host_dict[tmp1])
    elif tmp1 in host_dict.keys() and tmp2 in switch_dict.keys():
        host_dict[tmp1].add(switch_dict[tmp2])
        switch_dict[tmp2].add(host_dict[tmp1])
    elif tmp1 in switch_dict.keys() and tmp2 in host_dict.keys():
        host_dict[tmp2].add(switch_dict[tmp1])
        switch_dict[tmp1].add(host_dict[tmp2])
    else:
        switch_dict[tmp1].add(switch_dict[tmp2])
        switch_dict[tmp2].add(switch_dict[tmp1])

def set_topology():
    global host_dict, switch_dict
    hostlist = get_hosts().split(' ')
    switchlist = get_switches().split(' ')
    link_command = get_links().split(' ')
    ip_dic = get_ip()
    mac_dic = get_mac()
    
    host_dict = dict() # maps host names to host objects
    switch_dict = dict() # maps switch names to switch objects
    
    for h in hostlist:
        host_dict[h] = host(h, ip_dic[h], mac_dic[h])
        
    for s in switchlist:
        switch_dict[s] = switch(s)

    for link in link_command:
        nodes = link.split(',')
        add_link(nodes[0], nodes[1])

def ping(tmp1, tmp2): # initiate a ping between two hosts
    global host_dict, switch_dict
    if tmp1 in host_dict and tmp2 in host_dict: 
        node1 = host_dict[tmp1]
        node2 = host_dict[tmp2]
        node1.ping(node2.ip)
    else : 
        print("Invalid ping")

def show_table(target): # display the ARP or MAC table of a node
    if target in host_dict.keys():
        print("ip : mac")
        host_dict[target].show_table()

    elif target in switch_dict.keys():
        print("mac : port")
        switch_dict[target].show_table()

    elif target == "all_hosts":
        print("ip : mac")
        for host in host_dict.values():
            host.show_table()

    elif target == "all_switches":
        print("mac : port")
        for host in switch_dict.values():
            host.show_table()
    else:
        print("No such node")

def clear(target):
    if target in host_dict.keys():
        host_dict[target].clear()
    elif target in switch_dict.keys():
        switch_dict[target].clear()
    else:
        print("No such node")

def run_net():
    while(1):
        command = input(">> ")
        commandList = command.split(' ')
        if (len(commandList) == 3 and commandList[1] == "ping"):
            ping(commandList[0], commandList[2])

        elif (len(commandList) == 2 and commandList[0] == "show_table"):
            show_table(commandList[1])

        elif (len(commandList) == 2 and commandList[0] == "clear"):
            clear(commandList[1])
            
        else:
            print("a wrong command")
        print("")
    
def main():
    set_topology()
    run_net()


if __name__ == '__main__':
    main()
