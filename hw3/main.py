import protocols
from setting import Setting
import random
import matplotlib.pyplot as plt

def printRates(success_rate, idle_rate, collision_rate):
    print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=5, link_delay=0, seed=109550100)
printRates(*(protocols.aloha(setting, True)))
printRates(*(protocols.slotted_aloha(setting, True)))
printRates(*(protocols.csma(setting, True)))
printRates(*(protocols.csma_cd(setting, True)))

exit(0)

def plotThing(title: str, xlabel: str, ylabel: str, alohaList: list(), slotted_alohaList: list(), csmaList: list(), csma_cdList: list(), xList: list(), filename: str):
    plt.title(title)
    # plt.plot(xList, alohaList, marker='o', label='ALOHA')
    # plt.plot(xList, slotted_alohaList, marker='s', label='Slotted ALOHA')
    plt.plot(xList, csmaList, marker='D', label='CSMA')
    plt.plot(xList, csma_cdList, marker='*',label='CSMA/CD')
    plt.xticks(xList)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    # plt.show()
    plt.savefig('/Users/shflte/Desktop/hahahw3/' + filename + ".png")
    plt.clf()

aloha_success_rateList = []
slotted_aloha_success_rateList = []
csma_success_rateList = []
csma_cd_success_rateList = []

aloha_idle_rateList = []
slotted_aloha_idle_rateList = []
csma_idle_rateList = []
csma_cd_idle_rateList = []

aloha_collision_rateList = []
slotted_aloha_collision_rateList = []
csma_collision_rateList = []
csma_cd_collision_rateList = []
# 1.
# host_num_list = [2,3,4,6]
# packet_num_list = [1200,800,600,400] # To ensure that the total number of packets remains constant.
# settings = [Setting(host_num=h, packet_num=p, max_colision_wait_time=20, p_resend=0.3) for h,p in zip(host_num_list, packet_num_list)]

# 3. redo
# 4.
# settings = [Setting(coefficient=c) for c in range(1, 31)]
# 5.
# settings = [Setting(packet_num=p) for p in range(100, 1050, 50)]
# 6. 
# settings = [Setting(host_num=h) for h in range(1, 11)]
# 7. 
# settings = [Setting(packet_size=p) for p in range(1, 20)]
# 8.
link_delay_list= [0,1,2,3]
packet_size_list= [7,5,3,1] # To ensure that the packet_time remains constant.
settings = [Setting(link_delay=l, packet_size=p) for l,p in zip(link_delay_list, packet_size_list)]

for setting in settings:
    aloha_success_rate, aloha_idle_rate, aloha_collision_rate = protocols.aloha(setting, False)

    slotted_aloha_success_rate, slotted_aloha_idle_rate, slotted_aloha_collision_rate = protocols.slotted_aloha(setting, False)

    csma_success_rate, csma_idle_rate, csma_collision_rate = protocols.csma(setting, False)

    csma_cd_success_rate, csma_cd_idle_rate, csma_cd_collision_rate = protocols.csma_cd(setting, False)

    aloha_success_rateList.append(aloha_success_rate)
    slotted_aloha_success_rateList.append(slotted_aloha_success_rate)
    csma_success_rateList.append(csma_success_rate)
    csma_cd_success_rateList.append(csma_cd_success_rate)

    aloha_idle_rateList.append(aloha_idle_rate)
    slotted_aloha_idle_rateList.append(slotted_aloha_idle_rate)
    csma_idle_rateList.append(csma_idle_rate)
    csma_cd_idle_rateList.append(csma_cd_idle_rate)

    aloha_collision_rateList.append(aloha_collision_rate)
    slotted_aloha_collision_rateList.append(slotted_aloha_collision_rate)
    csma_collision_rateList.append(csma_collision_rate)
    csma_cd_collision_rateList.append(csma_cd_collision_rate)

xlist = link_delay_list
title = "Influence of Link Delay"
xlabel = "Link Delay"
# ylabel = 
plotThing(title, xlabel, "Success Rate", aloha_success_rateList, slotted_aloha_success_rateList, csma_success_rateList, csma_cd_success_rateList, xlist, "8-1")
plotThing(title, xlabel, "Idle Rate", aloha_idle_rateList, slotted_aloha_idle_rateList, csma_idle_rateList, csma_cd_idle_rateList, xlist, "8-2")
plotThing(title, xlabel, "Collision Rate", aloha_collision_rateList, slotted_aloha_collision_rateList, csma_collision_rateList, csma_cd_collision_rateList, xlist, "8-3")

