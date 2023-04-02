#include <iostream>
#include <stdlib.h>
#include <pcap/pcap.h> 
#include <string.h>
#include <string>
#include <getopt.h>
#include <vector>
#include <sys/cdefs.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/if_ether.h>
#include <features.h>

using namespace std;
int numPackets = -1;
string filter = "all";
string interface;

struct iphdr
  {
#if __BYTE_ORDER == __LITTLE_ENDIAN
    unsigned int ihl:4;
    unsigned int version:4;
#elif __BYTE_ORDER == __BIG_ENDIAN
    unsigned int version:4;
    unsigned int ihl:4;
#else
# error        "Please fix <bits/endian.h>"
#endif
    u_int8_t tos;
    u_int16_t tot_len;
    u_int16_t id;
    u_int16_t frag_off;
    u_int8_t ttl;
    u_int8_t protocol;
    u_int16_t check;
    u_int32_t saddr;
    u_int32_t daddr;
    /*The options start here. */
  };
struct tcphdr
  {
    u_int16_t source;
    u_int16_t dest;
    u_int32_t seq;
    u_int32_t ack_seq;
#  if __BYTE_ORDER == __LITTLE_ENDIAN
    u_int16_t res1:4;
    u_int16_t doff:4;
    u_int16_t fin:1;
    u_int16_t syn:1;
    u_int16_t rst:1;
    u_int16_t psh:1;
    u_int16_t ack:1;
    u_int16_t urg:1;
    u_int16_t res2:2;
#  elif __BYTE_ORDER == __BIG_ENDIAN
    u_int16_t doff:4;
    u_int16_t res1:4;
    u_int16_t res2:2;
    u_int16_t urg:1;
    u_int16_t ack:1;
    u_int16_t psh:1;
    u_int16_t rst:1;
    u_int16_t syn:1;
    u_int16_t fin:1;
#  else
#   error "Adjust your <bits/endian.h> defines"
#  endif
    u_int16_t window;
    u_int16_t check;
    u_int16_t urg_ptr;
};
struct udphdr
{
  u_int16_t source;
  u_int16_t dest;
  u_int16_t len;
  u_int16_t check;
};
struct icmphdr {
    u_int8_t type;
    u_int8_t code;
    u_int16_t checksum;
};



void parseArg(int argc, char *argv[]) {
    const char *optstring = "i:c:f:";
    int c;
    struct option opts[] = {
        {"interface", 1, NULL, 'i'},
        {"count", 1, NULL, 'c'},
        {"filter", 1, NULL, 'f'}
    };

    while((c = getopt_long(argc, argv, optstring, opts, NULL)) != -1) {
        switch(c) {
            case 'i':
                interface = string(optarg);
                break;
            case 'c':
                numPackets = stoi(string(optarg));
                break;
            case 'f':
                filter = string(optarg);
                if (filter != "all" && filter != "tcp" && filter != "udp" && filter != "icmp") {
                    cerr << "Invalid argument for filter: " << filter << endl;
                    exit(-1);
                }
                if (filter == "tcp") {
                    filter = "tcp and not port ssh";
                }
                else if (filter == "all") {
                    filter = "not port ssh";
                }
                break;
            case '?':
                printf("unknown option\n");
                break;
            default:
                printf("------\n");

        }
    }
}

int main(int argc, char *argv[]) {
    parseArg(argc, argv);

    pcap_if_t *devices = NULL; 
    char errbuf[PCAP_ERRBUF_SIZE];
    char ntop_buf[256];
    struct ether_header *eptr;
    vector<pcap_if_t*> vec; // vec is a vector of pointers pointing to pcap_if_t 

    //get all devices 
    if(-1 == pcap_findalldevs(&devices, errbuf)) {
        fprintf(stderr, "pcap_findalldevs: %s\n", errbuf); // if error, fprint error message --> errbuf
        exit(1);
    }

    //list all device
    int cnt = 0;
    for(pcap_if_t *d = devices; d ; d = d->next, cnt++)
    {
        vec.push_back(d);
        cout<<"Name: "<<d->name<<endl;
    }
    cout << endl;

    struct bpf_program fp; // for filter, compiled in "pcap_compile"
    pcap_t *handle;
    handle = pcap_open_live(interface.c_str(), 65535, 1, 1, errbuf);  
    //pcap_open_live(device, snaplen, promise, to_ms, errbuf), interface is your interface, type is "char *"   

    if(!handle|| handle == NULL)
    {
        fprintf(stderr, "pcap_open_live(): %s\n", errbuf);
        exit(1);
    }
 
    if(-1 == pcap_compile(handle, &fp, {filter.c_str()}, 1, PCAP_NETMASK_UNKNOWN) ) // compile "your filter" into a filter program, type of {your_filter} is "char *"
    {
        pcap_perror(handle, "pkg_compile compile error\n");
        exit(1);
    }
    if(-1 == pcap_setfilter(handle, &fp)) { // make it work
        pcap_perror(handle, "set filter error\n");
        exit(1);
    }

    const unsigned char *packet;
    // struct ether_header *ethptr;
    struct iphdr *ipptr;
    struct tcphdr *tcpptr;
    struct udphdr *udpptr;
    struct icmphdr *icmpptr;
    int iphdlen;
    char *payload;
    int payloadlen;
    int totallen;
    for (int t = 0; t < numPackets || numPackets == -1; t++) {
        pcap_pkthdr header;
        packet = pcap_next(handle, &header);
        ipptr = (struct iphdr *)(packet + 14);
        iphdlen = ipptr->ihl * 4;
        char payloadbuf[20];
        bzero(payloadbuf, sizeof(payloadbuf));

        struct in_addr ip_addr;

        switch (ipptr->protocol) {
        case 1: // icmp
            icmpptr = (struct icmphdr *)(packet + 14 + 20);
            cout << "Transport type: ICMP" << endl;
            ip_addr.s_addr = ipptr->saddr;
            printf("Source IP: %s\n", inet_ntoa(ip_addr));
            ip_addr.s_addr = ipptr->daddr;
            printf("Destination IP: %s\n", inet_ntoa(ip_addr));
            printf("ICMP type value: %d\n", icmpptr->type);
            cout << endl;
            break;
        case 6: // tcp
            cout << "Transport type: TCP" << endl;
            ip_addr.s_addr = ipptr->saddr;
            printf("Source IP: %s\n", inet_ntoa(ip_addr));
            ip_addr.s_addr = ipptr->daddr;
            printf("Destination IP: %s\n", inet_ntoa(ip_addr));
            tcpptr = (struct tcphdr *)(packet + 14 + 20);
            printf("Source port: %d\n", ntohs(tcpptr->source));
            printf("Destination port: %d\n", ntohs(tcpptr->dest));
            payload = (char *)(packet + 14 + 20 + tcpptr->doff * 4);
            payloadlen = ntohs(ipptr->tot_len) - 20 - tcpptr->doff * 4;
            payloadlen = payloadlen >= 16 ? 16 : payloadlen;
            memcpy(payloadbuf, payload, payloadlen);
            printf("Payload: ");
            for (int i = 0; i < payloadlen; i++) {
                printf("%x ", payload[i]);
            }
            printf("\n");
            cout << endl;
            break;
        case 17: // udp
            cout << "Transport type: UDP" << endl;
            ip_addr.s_addr = ipptr->saddr;
            printf("Source IP: %s\n", inet_ntoa(ip_addr));
            ip_addr.s_addr = ipptr->daddr;
            printf("Destination IP: %s\n", inet_ntoa(ip_addr));
            udpptr = (struct udphdr *)(packet + 14 + 20);
            printf("Source port: %d\n", ntohs(udpptr->source));
            printf("Destination port: %d\n", ntohs(udpptr->dest));
            payload = (char *)(packet + 14 + 20 + 8);
            payloadlen = ntohs(ipptr->tot_len) - 20 - 8;
            payloadlen = payloadlen >= 16 ? 16 : payloadlen;
            memcpy(payloadbuf, payload, payloadlen);
            printf("Payload: ");
            for (int i = 0; i < payloadlen; i++) {
                printf("%x ", payload[i]);
            }
            printf("\n");
            cout << endl;
            break;
        default:
            t--;
            break;
        }
        if (numPackets == -1) t = 0;
    }

    pcap_freealldevs(devices);

    return 0;
    
}