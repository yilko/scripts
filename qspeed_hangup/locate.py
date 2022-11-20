from airtest.core.api import *;
import start_border;

locate_path = "photo/locate";
going_path = "photo/going";
photo_path = "photo";


# 定位所在位置
def loc_address():
    # 在边境房间(或者是结算页面，存在没有返回成功情况)
    if exists(Template(locate_path + r"\在边境房.png", threshold=0.8)):
        # 小概率存在点了返回但是无响应的情况，此时会一直停留在结算页面
        if exists(Template(photo_path + r"\返回房间.png")):
            back_loc = wait(Template(photo_path + r"\返回房间.png"), timeout=10, interval=1);
            double_click(back_loc);
    # 在边境页面
    elif exists(Template(locate_path + r"\在边境主页.png", threshold=0.8)):
        border_page_to_room();
    # 在大厅
    elif exists(Template(locate_path + r"\在大厅.png", threshold=0.8)):
        home_to_room();
    # 在排位页面
    elif exists(Template(locate_path + r"\在排位.png", threshold=0.8)):
        rank_to_room();
    # 在跑图页面(解决匹配20秒后才进图的问题)
    elif exists(Template(locate_path + r"\跑图页面.png", threshold=0.7)):
        start_border.hang_up();
    # else:
    #     keyevent("26");
    #     raise Exception("五个页面都不在，息屏！");


# 大厅到边境房间
def home_to_room():
    match_loc = wait(Template(locate_path + r"\在大厅.png"), timeout=10, interval=1);
    click(match_loc);
    rank_to_room();


# 排位页面到边境房间
def rank_to_room():
    border_loc = wait(Template(going_path + r"\点击左侧边境战争.png"), timeout=10, interval=1);
    click(border_loc);
    # 排位也有个人竞速按钮，切换时先睡一下,避免识别到排位的个人竞速
    sleep(0.5);
    border_page_to_room();


# 边境页面到边境房间
def border_page_to_room():
    person_speed_loc = wait(Template(going_path + r"\点击边境个人竞速.png", threshold=0.8), timeout=10, interval=1);
    click(person_speed_loc);
    coupon_60_loc = wait(Template(going_path + r"\点击60点券.png"), timeout=10, interval=1);
    click(coupon_60_loc);
