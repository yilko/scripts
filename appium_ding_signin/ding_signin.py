import os
import time

from appium import webdriver;
from selenium.webdriver.common.by import By
from apscheduler.schedulers.blocking import BlockingScheduler;

'''实现钉钉自动打卡,未屏蔽敏感字段'''


class DingSignin:

    def __init__(self):
        # 192.168.xxx.xxx:5555
        self.driver = self.__desired_caps("xxx");
        self.pwd = "xxx";
        # 包名和界面通过命令获取：adb shell dumpsys activity activities | findstr /i mResumedActivity
        self.package, self.activity = "com.alibaba.android.rimet", ".biz.LaunchHomeActivity";

    # appium连接配置
    def __desired_caps(self,device_name) -> webdriver:
        url = "http://localhost:4723/wd/hub";
        desired_caps = {"platformName": "Android", "platformVersion": "10", "noReset": True,
                        "autoGrantPermissions": True, "deviceName": device_name};
        driver = webdriver.Remote(url, desired_caps);
        return driver;

    # 检查屏幕是否亮起
    @staticmethod
    def __check_screen() -> bool:
        screen_cmd = "adb shell dumpsys window policy | findstr screenState";
        content = os.popen(screen_cmd).read();
        return True if "on" in content.lower() else False;

    # 检查是否已经解锁
    @staticmethod
    def __check_unlock() -> bool:
        unlock_cmd = "adb shell dumpsys window policy | findstr mInputRestricted";
        # 返回InputRestricted为true说明输入受限制，也就是需要输入密码,false代表解锁
        content = os.popen(unlock_cmd).read();
        return True if "false" in content.lower() else False;

    # 滑动进入解锁页面
    def swipe_to_input_pwd(self):
        screen_size = self.driver.get_window_size();
        x, y = screen_size["width"], screen_size["height"];
        self.driver.swipe(0.5 * x, 0.75 * y, 0.5 * x, 0.25 * y, 200);

    # 输入密码
    def input_pwd(self):
        for i in list(self.pwd):
            self.driver.find_element(By.XPATH, f'//*[@text="{i}"]').click();

    # 手机解锁
    def unlock_phone(self):
        screen_flag = DingSignin.__check_screen();
        unlock_flag = DingSignin.__check_unlock();
        # 已亮屏未解锁(都是这种场景居多，appium连接手机都会亮屏)
        if screen_flag is True and unlock_flag is False:
            self.swipe_to_input_pwd();
            self.input_pwd();
        # 已亮屏已解锁
        elif screen_flag and unlock_flag:
            pass;
        # 未亮屏未解锁(基本没有该场景)
        elif screen_flag is False and unlock_flag is False:
            os.popen("adb shell input keyevent 26");
            # 等响应需要一定时间，睡3s
            time.sleep(3);
            self.swipe_to_input_pwd();
            self.input_pwd();
        # 未亮屏已解锁
        else:
            raise Exception(f"屏幕状态===={screen_flag}，解锁状态{unlock_flag}");

    # 打开钉钉签到
    def start_ding(self):
        self.driver.start_activity(self.package, self.activity);
        self.driver.implicitly_wait(5);
        work_bench_loc = '//*[@text="工作台"]';
        self.driver.find_element(By.XPATH, work_bench_loc).click();
        self.driver.implicitly_wait(5);
        kaoqin_loc = '//*[@text="考勤打卡"]';
        self.driver.find_element(By.XPATH, kaoqin_loc).click();
        self.driver.implicitly_wait(5);
        clock_in_loc = '//*[@text="上班打卡"]';
        self.driver.find_element(By.XPATH, clock_in_loc).click()

    # 关闭退出
    def close_quit(self):
        self.driver.terminate_app(self.driver.current_package);
        # 如果退出driver会导致下次签到出问题，除非重新开driver
        # self.driver.quit();
        os.popen("adb shell input keyevent 26");

    # 程序主入口
    def main(self):
        self.unlock_phone();
        print("解锁成功");
        self.start_ding();
        print("签到成功");
        self.close_quit();

    # 定时任务
    def timing(self):
        block_sched = BlockingScheduler(timezone="Asia/Shanghai");
        # 0-6代表周一到周七
        block_sched.add_job(self.main, "cron", day_of_week="0-6", hour="16", minute="05,06");
        print("开始等待...");
        block_sched.start();


if __name__ == '__main__':
    ding = DingSignin();
    ding.timing();
    # ding.main();
