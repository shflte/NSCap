import protocols
from setting import Setting
import random

print("aloha")
setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=109550171)
# setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1)
success_rate, idle_rate, collision_rate = protocols.aloha(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("slotted_aloha")
setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=109550171)
# setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1)
success_rate, idle_rate, collision_rate = protocols.slotted_aloha(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("csma")
setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=109550171)
# setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1)
success_rate, idle_rate, collision_rate = protocols.csma(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')

print("csma_cd")
setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=109550171)
# setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1)
success_rate, idle_rate, collision_rate = protocols.csma_cd(setting, True)
print(f'success_rate: {success_rate}\nidle_rate: {idle_rate}\ncollision_rate: {collision_rate}\n')
