import re
import os
import matplotlib.pyplot as plt

filename = 'result.txt'
height_range_list = []
tilt_servo_angle_list = []
with open(filename, 'r') as result:
    for line_index,line in enumerate(result):
        processed = line.strip()
        # print(processed[0:4])
        
        #Nyari selisih angle
        if processed[0:11] == 'servo angle':
            selisih = len(height_range_list) - len(tilt_servo_angle_list)
            if selisih > 1:
                for _ in range(selisih-1):
                    tilt_servo_angle_list.append(tilt_servo_angle_list[-1])
            tilt_servo_angle = (float(processed[12:]))
            tilt_servo_angle_list.append(tilt_servo_angle)
            # # print(pan_servo_angle)
            # selisih = len(width_range_list) - len(pan_servo_angle_list)
        
        #Nyari width range
        if processed[0:12] == 'height range':
            height_range = (float(processed[13:]))
            height_range_list.append(height_range)

selisih_akhir = len(height_range_list) - len(tilt_servo_angle_list)
for _ in range(selisih_akhir):
    tilt_servo_angle_list.append(tilt_servo_angle_list[-1])
# print(len(height_range_list))
# print(len(tilt_servo_angle_list))
height_range_list = height_range_list[15:]
index = range(len(height_range_list))
# plt.plot(index,width_range_list,'r')
# plt.title('Grafik Width Range')
# plt.xlabel('Frame')
# plt.ylabel('Width Range')
# plt.yticks(range(-200,201,40))
# plt.xticks(range(0,601,50))
# # plt.figure()

tilt_servo_angle_list = tilt_servo_angle_list[15:]
# pan_index = range(len(pan_servo_angle_list))
# plt.plot(pan_index,pan_servo_angle_list)
# plt.title('Grafik Pan Servo Angle')
# plt.xlabel('Frame')
# plt.xticks(range(0,601,50))
# plt.ylabel('Pan Servo Angle')

# plt.show()
fig, ax1 = plt.subplots()
color = 'tab:red'
ax1.set_xlabel('Frame')
ax1.set_yticks(range(-210,211,30))
ax1.set_ylabel('Error Y', color=color)
ax1.plot(index, height_range_list, color=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('Servo Angle', color=color)  # we already handled the x-label with ax1
ax2.plot(index, tilt_servo_angle_list, color=color)
# ax2.tick_params(axis='y', labelcolor=color)


fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()
