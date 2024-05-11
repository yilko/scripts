import os
import re
import csv
import time
from datetime import datetime

'''
对设备进行无线连接并且保存设备信息
'''


class ConnectAdb:
    def __init__(self):
        self.device_num, self.brand = self.__check_wired_connected();
        self.host = self.__connect_adb();

    # 检查是否有线连接手机和获取手机牌子
    @staticmethod
    def __check_wired_connected():
        for i in range(3):
            brand = os.popen("adb -d shell getprop ro.product.brand").read().strip();
            content = os.popen("adb devices").read();
            # 读取到的内容默认带上换行符，去掉后在判断包含关系
            device_num = os.popen("adb -d get-serialno").read().strip();
            if device_num != "" and device_num in content:
                return device_num, brand;
            else:
                print(f"暂时还没获取到设备号，正在重试第{i + 1}次...");
                time.sleep(2);
        else:
            raise Exception("----------没有有线连接手机,或者电脑没有连接上手机----------");

    # 获取手机ip并进行无线连接
    @staticmethod
    def __connect_adb():
        content = os.popen("adb -d shell ip addr show wlan0").read();
        host = re.findall("inet\s(\d.*?)/", content)[0];
        os.popen("adb -d tcpip 5555");
        os.popen(f"adb -d connect {host}:5555");
        return host;

    # 检查是否连上无线连接
    def check_wireless_connected(self):
        # 睡一秒保证adb连上无线连接
        time.sleep(1);
        content = os.popen("adb devices").read();
        if self.host not in content:
            raise Exception("----------没有成功改为无线连接！建议重新执行该脚本或手动进行adb无线连接！----------");
        else:
            print(f"----------已成功无线连接，ip为{self.host}----------");

    # 记录下手机牌子，序列号，ip，时间到csv文件中，后续截图需要获取csv文件的ip
    # 四种场景：
    # 1.没有csv自动创建并添加
    # 2.有csv无内容直接追加
    # 3.csv有内容但没有遍历到所需设备，直接追加
    # 4.csv有内容且遍历到所需设备，修改该行数据
    def markdown(self):
        # 路径要写绝对路径，否则通过cmd创建的文件不在这个目录下
        parent_path = os.path.dirname(__file__) + os.path.sep;
        # a+模式可以在无文件时自动创建
        # a+和seek方法共用可以避免无文件报错并且能读取到原数据，两者兼得
        # 而单纯的r或r+模式，只能读到原数据，但在文件不存在时打开会报错
        with open(parent_path + "mark_ip.csv", "a+") as f:
            # a+模式打开文件时，文件指针会定位到文件的末尾
            # 需要移动指针到开始位置，才能读取文件原数据
            f.seek(0);
            r = csv.reader(f);
            content = list(r);
            # print("-------------",content)

        with open(parent_path + "mark_ip.csv", "w", newline='') as f:
            w = csv.writer(f);
            ts = datetime.now().strftime("%F %T");
            update_row = [self.brand, self.device_num, self.host, 5555, ts];
            is_update_flag = False;
            if content:
                for line in content:
                    if self.brand in line[0]:
                        is_update_flag = True;
                        w.writerow(update_row);
                    else:
                        w.writerow(line);
                else:
                    # 遍历完都没有更新到，追加一行
                    if not is_update_flag:
                        w.writerow(update_row);
            # csv无内容直接添加
            else:
                w.writerow(update_row);


if __name__ == '__main__':
    print("----------该脚本用于无线连接----------");
    print("----------需要确保你的手机处于开发者模式并且是usb可调试状态，如有不懂请百度----------");
    print("----------建议插入数据线后，等电脑右下角出现识别到设备后再选择，或者等2-3秒选择----------");
    time.sleep(1);
    ca = ConnectAdb();
    ca.check_wireless_connected();
    ca.markdown();
