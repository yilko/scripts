该脚本通过adb进行手机截图并发送到电脑
1.手机需要先打开开发者模式并且是usb可调试状态
2.数据线连接手机和电脑，点击conn.bat脚本，会自动从有线连接改为无线连接
3.当看到ip为xxxx说明改为无线连接，此时可以拔掉数据线
4.conn.bat脚本执行成功后会有一个mark_ip.csv文件
5.分别记录手机品牌，手机序列号，手机无线连接ip，端口，时间戳
6.需要参考mi.bat脚本，把Xiaomi这个手机品牌的参数改为你实际手机的品牌(mark_ip.csv可看到)
7.改好品牌后，当需要截图时双击mi.bat即可
8.截图的图片在手机和电脑中都有固定的存放位置，手机存放路径为/sdcard/save_files/，电脑存放位置是当前脚本目录下，都会以当天时间起一个文件夹，当天图片放当天文件夹