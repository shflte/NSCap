from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Switch, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}
        self.target_ports = [3, 4]  # Target ports to be dropped

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the default_table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, 0)  # Priority 0 for default_table

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst, table_id=table_id)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # Table 0: default_table
        # Priority 0: Send to filter_table_1
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]  # Send to next table
        self.add_flow(datapath, 0, match, actions, 0)

        # Table 1: filter_table_1
        # Priority 0: ICMP packets go to filter_table_2, others go to forward_table
        match = parser.OFPMatch(eth_type=eth_pkt.ethertype)
        if eth_pkt.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            if ip_pkt.proto == inet.IPPROTO_ICMP:
                actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]  # Send to filter_table_2
                self.add_flow(datapath, 0, match, actions, 1)
            else:
                actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]  # Send to forward_table
                self.add_flow(datapath, 1, match, actions, 1)

        # Table 2: filter_table_2
        # Priority 0: Drop packets coming from target_ports, others go to forward_table
        match = parser.OFPMatch(in_port=in_port)
        if in_port in self.target_ports:
            actions = []  # Drop the packet
            self.add_flow(datapath, 0, match, actions, 2)
        else:
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]  # Send to forward_table
            self.add_flow(datapath, 1, match, actions, 2)

        # Table 3: forward_table
        # Priority 1: Forward the packet
        match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]  # Forward the packet
        self.add_flow(datapath, 1, match, actions, 3)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
