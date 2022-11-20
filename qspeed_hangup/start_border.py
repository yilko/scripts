from datetime import datetime

from airtest.core.api import *;
import locate;

photo_path = "photo";
refuse_path = "photo/refuse";
end_flag_path = "photo/end_flag";
locate_path = "photo/locate";


# 关闭别人的弹窗邀请
def close_invite():
    if exists(Template(refuse_path + r"\他人邀请.png")):
        click(Template(refuse_path + r"\拒绝邀请.png"));
        click(Template(refuse_path + r"\发送拒绝邀请.png"));


# 检查次数是否为0
def check_border_count():
    if exists(Template(end_flag_path + r"\次数已满.png", threshold=0.9)):
        keyevent("26");
        raise Exception("次数没了，息屏！");


# 每次返回页面检查是否超过十一点
def check_time():
    hour = int(datetime.now().hour);
    if hour > 22:
        keyevent("26");
        raise Exception("到点了，息屏！");
    else:
        return True;


# 一直循环，每隔20秒检查是否出现结算标志位
def hang_up():
    # 这里不能写check_time()，可能存在到了十一点还在挂机的情况，写check_time()会在挂机途中就息屏了
    while True:
        sleep(20);
        # 不需要对中途断网进行处理，飞车断网，adb也会断网，无法做任何操作
        # 20秒醒来后判断是否出现结算标志位，如果出现则返回房间继续下次循环，没有则继续睡眠等待
        if exists(Template(photo_path + r"\结束页面.png")):
            click(Template(photo_path + r"\点击继续.png"));
            back_loc = wait(Template(photo_path + r"\返回房间.png"), timeout=10, interval=1);
            # 防止点一次无响应，改为双击
            double_click(back_loc);
            break;
        # 可能会有手贱自己点了结算页面，会自动返回房间,此时退出循环
        elif exists(Template(locate_path + r"\在边境房.png")):
            break;


# 边境开始结束返回(点击到正式跑大概用20s，倒计时10s，结算10s)
def start_end():
    while check_time():
        # 点击开始匹配边境
        try:
            # 0.988才能比较精准识别页面是否被别人邀请，触发关闭邀请后重新开始
            start_loc = wait(Template(photo_path + r"\匹配边境.png", threshold=0.988), timeout=10, interval=1);
            # 可能存在已经匹配图片，但是还不能点击情况，睡0.5秒防止该情况(结算页面返回房间会出现)
            sleep(0.5);
            double_click(start_loc);
        except TargetNotFoundError:
            # 次数已经为零(弹窗)/找不到匹配边境按钮说明页面被别人邀请挡住/网络差回到边境页面
            check_border_count();
            close_invite();
            locate.loc_address();
            continue;
        try:
            # 确认在进图页面
            wait(Template(photo_path + r"\放弃禁用.png"), timeout=20, interval=1);
            hang_up();
        except TargetNotFoundError:
            # 点击开始后没有进入进图页面，考虑为次数已经为零，匹配超过40秒都没进图还在边境房
            continue;


if __name__ == '__main__':
    auto_setup(__file__, devices=["Android:///"]);
    start_end();

    # 调试adb是否运行
    # auto_setup(__file__, devices=["Android:///"]);
    # keyevent("26");
    # swipe((500, 1500), (500, 500), duration=0.05);
