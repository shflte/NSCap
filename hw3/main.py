import protocols
from setting import Setting
import random
import matplotlib.pyplot as plt

def plotThing(title: str, xlabel: str, ylabel: str, alohaList: list(), slotted_alohaList: list(), csmaList: list(), csma_cdList: list(), xList: list()):
    plt.title(title)
    plt.plot(xList, alohaList, marker='o', label='ALOHA')
    plt.plot(xList, slotted_alohaList, marker='s', label='Slotted ALOHA')
    plt.plot(xList, csmaList, marker='D', label='CSMA')
    plt.plot(xList, csma_cdList, marker='*',label='CSMA/CD')
    plt.xticks(xList)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.show()

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

host_num_list = [2,3,4,6]
packet_num_list = [1200,800,600,400] # To ensure that the total number of packets remains constant.
settings = [Setting(host_num=h, packet_num=p, max_colision_wait_time=20, p_resend=0.3) for h, p in zip(host_num_list, packet_num_list)]

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

plotThing()