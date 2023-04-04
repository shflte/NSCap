import protocols
from setting import Setting
import random

def plt():
    aloha_success=[]
    slotted_aloha_success=[]
    csma_success=[]
    csma_cd_success=[]

    aloha_success.append(success_rate)
    slotted_aloha_success.append(success_rate)
    csma_success.append(success_rate)
    csma_cd_success.append(success_rate)

    plt.plot(host_num_list, aloha_success, marker='o', label='ALOHA')
    plt.plot(host_num_list, slotted_aloha_success, marker='s', label='Slotted ALOHA')
    plt.plot(host_num_list, csma_success, marker='D', label='CSMA')
    plt.plot(host_num_list, csma_cd_success, marker='*',label='CSMA/CD')
    plt.xticks(host_num_list)
    plt.xlabel('Number of Hosts')
    plt.ylabel('Success Rate')
    plt.legend()
    plt.show()

# setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=5, link_delay=1, seed=11234)
setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=4)

print("aloha")
success_rate, idle_rate, collision_rate = protocols.aloha(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("slotted_aloha")
success_rate, idle_rate, collision_rate = protocols.slotted_aloha(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("csma")
success_rate, idle_rate, collision_rate = protocols.csma(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("csma_cd")
success_rate, idle_rate, collision_rate = protocols.csma_cd(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')
