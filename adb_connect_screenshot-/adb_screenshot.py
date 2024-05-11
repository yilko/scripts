import csv
import os
import sys
import time
from datetime import datetime

'''
adb连接的情况下，支持以天为单位创文件夹，把手机截图的图片传到电脑并打开图片
'''


class AdbScreenshot:

    def __init__(self):
        # 定义手机和电脑的存放图片根目录，不能在本地删除
        self.phone_root_path = r"/sdcard/save_files/";
        self.pc_root_path = os.path.dirname(__file__) + os.path.sep + "save_files" + os.path.sep;
        self.brand, self.host = self.__get_params();
        self.__check_wireless_connected();
        self.phone_path, self.pc_path = self.__check_directory();

    # 获取cmd脚本传参(设备)和csv数据信息
    @staticmethod
    def __get_params():
        brand = sys.argv[1];
        parent_path = os.path.dirname(__file__) + os.path.sep;
        with open(parent_path + "mark_ip.csv") as f:
            r = csv.reader(f);
            for line in r:
                if brand == line[0]:
                    return line[0], f"{line[2]}:{line[3]}";

    # 检查是否连上无线连接
    def __check_wireless_connected(self):
        content = os.popen("adb devices").read();
        if self.host not in content:
            raise Exception("----------没有检测到无线连接的ip！建议重新连接adb----------");

    # 检查手机和电脑是否创建了当天文件夹
    def __check_directory(self):
        today = datetime.now().strftime("%F");
        # 检查手机目录
        check_dir_cmd = f"adb -s {self.host} shell ls {self.phone_root_path} | findstr /i {today}";
        content = os.popen(check_dir_cmd).read();
        if content == "":
            mkdir_cmd = f"adb -s {self.host} shell mkdir {self.phone_root_path}{today}";
            os.popen(mkdir_cmd);
        # 检查电脑目录
        pc_path = self.pc_root_path + today + os.path.sep;
        if not os.path.exists(pc_path):
            os.mkdir(pc_path);
        return self.phone_root_path + today + "/", pc_path;

    # adb截图，推到电脑，打开截图
    def sc_pull_open(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S");
        photo_name = f"{self.brand}_sc_{ts}.png";
        photo_path = self.phone_path + photo_name;
        os.popen(f"adb -s {self.host} shell screencap {photo_path}");
        # 睡一秒以防还没生成文件就pull，会pull不到
        time.sleep(1);
        os.popen(f"adb -s {self.host} pull {photo_path} {self.pc_path}");
        time.sleep(1);
        try:
            os.startfile(self.pc_path + photo_name);
        except FileNotFoundError:
            time.sleep(2);
            os.startfile(self.pc_path + photo_name);


if __name__ == '__main__':
    ass = AdbScreenshot();
    ass.sc_pull_open();
