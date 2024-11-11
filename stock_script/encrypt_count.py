import binascii
import os.path
import sys
import uuid
import winreg as reg
from datetime import datetime, timedelta
import aes_encrypt_module as aem

'''
该脚本主要限制程序调用次数

主要功能：
1、mac地址、时间戳、运行次数三者使用aes加密放到隐藏文件中，同时写入注册表
2、mac地址防止他人分享，时间戳防止他人修改文件内容(校验文件修改时间)，注册表防止备份之前文件使用
3、生成的默认文件，当天有效，第二天无效(程序当天激活)

已考虑的破解场景：
1、删除文件，报错提示
2、次数达到上限，报错提示
3、修改文件内容，报错提示
4、默认文件的内容复制到已达上限的文件(次数满了以为复制原字符串可以重置0)，报错提示
5、备份多份默认文件，过期后就替换新的默认文件，报错提示(当天必须激活一次程序来避免该情况)
6、备份多份在使用的文件，报错提示(把之前执行次数没到上限的文件复制使用)
'''


# 创建默认文件，只有该文件的修改时间可使用
def create_default_file(encrypt_path: str):
    now = datetime.now()
    with open(encrypt_path, 'w') as f:
        content = f"yilko_{now.strftime('%Y%m%d_%H%M%S')}_0"
        # content = 'yilko_20241030_000000_0'
        # content = f"6807151bf1ec_{now.strftime('%Y%m%d_%H%M%S')}_10"
        encrypt_str = aem.aes_cbc_encode("yilko_aespwd_key", "yilko_aespwd_kiv", content, "utf-8")
        f.write(encrypt_str)
    ts = now.timestamp()
    # ts = datetime(2024, 10, 30, 00, 00, 00).timestamp()
    os.utime(encrypt_path, (ts, ts))
    os.system(f'attrib +h "{encrypt_path}"')


class EncryptCount:
    def __init__(self, encrypt_path, count: int, key_path: str, key_name: str):
        self.encrypt_path = encrypt_path
        self.key, self.iv, self.charset = "yilko_aespwd_key", "yilko_aespwd_kiv", "utf-8"
        self.count = count
        self.key_path = key_path
        self.key_name = key_name

    # 读取文件解密
    def get_file_content(self):
        try:
            with open(self.encrypt_path, 'r') as f:
                encrypt_content = f.read()
                content = aem.aes_cbc_decode(self.key, self.iv, encrypt_content, self.charset)
                # print(content)
                return content
        except binascii.Error:
            print('相关配置文件被改动[d]，程序无法执行，请联系相关人员')
            sys.exit(1)

    # 检查文件和内容的时间，防止他人修改文件内容
    def __check_time(self, file_content: str):
        # 文件内容时间
        c_date, c_time = file_content.split('_')[1], file_content.split('_')[2]
        content_time = datetime.strptime(f'{c_date}_{c_time}', '%Y%m%d_%H%M%S')
        # 文件修改时间
        ts = os.path.getmtime(self.encrypt_path)
        file_time = datetime.fromtimestamp(ts)
        # print(f'文本内容时间===={content_time}', f'文件修改时间===={file_time}')
        # 正常写入内容的时间和文件修改时间是一致的，预防有时间间隔，减30s
        # 如果修改过文件，文件的时间一定会比内容的时间大，证明有人改过文件
        if content_time < file_time + timedelta(seconds=-30):
            print(f'相关配置文件被改动[t]，程序无法执行，请联系相关人员')
            sys.exit(1)
        return content_time

    # 检查mac地址,首次激活后都会读取和写入mac地址,防止他人分享
    @staticmethod
    def __check_mac_address(file_content: str):
        mac_or_yilko, count = file_content.split('_')[0], int(file_content.split('_')[-1])
        mac_address = '{:012x}'.format(uuid.getnode())
        # 默认文件的salt是yilko，当激活后次数不会存在0的情况，此时都是录入mac地址
        if count != 0 and mac_or_yilko != mac_address:
            print(f'程序仅限本电脑使用，禁止分享给他人使用')
            print(mac_address)
            sys.exit(1)
        return mac_address

    # 检查注册表，防止他人备份已有的config文件重复执行
    def check_regedit(self, file_content: str):
        count = int(file_content.split('_')[-1])
        if count != 0:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.key_path, 0, reg.KEY_ALL_ACCESS)
            content, content_type = reg.QueryValueEx(key, self.key_name)
            with open(self.encrypt_path, 'r') as f:
                f_content = f.read();
            # print(content, f_content)
            if content != f_content:
                print('相关配置文件被改动[r]，程序无法执行，请联系相关人员')
                sys.exit(1)

    # 不满足更新条件的场景
    def __check_mismatch_condition(self, file_content: str):
        content_time = self.__check_time(file_content)
        mac_address = self.__check_mac_address(file_content)
        self.check_regedit(file_content)
        count = int(file_content.split('_')[-1])
        now = datetime.now()
        # print(f'文本内容时间===={content_time}', f'插入内容时间===={now}')
        if content_time.date() == now.date() and count > self.count - 1:
            print(f'----------每日可运行{self.count}次，今天为第{count}次，次数已用完，请明天再执行----------')
            sys.exit(1)
        # 防止别人重复拿生成的默认文件来破解，当天没有把默认文件的0次数改为1，第二天都过期不能用
        elif content_time.date() < now.date() and count == 0:
            print(f'----------程序当天没有首次激活运行，已过期，请联系相关人员----------')
            sys.exit(1)
        # 时间跳到第二天时，count重置
        elif content_time.date() < now.date():
            count = 0
        count += 1
        return mac_address, now.strftime("%Y%m%d_%H%M%S"), count

    # 更新文件内容
    def update_file(self, file_content: str):
        mac_address, content_time, count = self.__check_mismatch_condition(file_content)
        new_content = f'{mac_address}_{content_time}_{count}'
        encrypt_str = aem.aes_cbc_encode(self.key, self.iv, new_content, self.charset)
        # print(new_content, encrypt_str)
        # 文件隐藏时因为权限问题无法写入，先取消隐藏，写入后再隐藏
        os.system(f'attrib -h "{self.encrypt_path}"')
        with open(self.encrypt_path, 'w') as f:
            f.write(encrypt_str)
        os.system(f'attrib +h "{self.encrypt_path}"')
        # 写入注册表
        self.update_regedit(encrypt_str)
        print(f'----------每日可运行{self.count}次，今天为第{count}次----------')

    # 加密字符串同步更新到注册表
    def update_regedit(self, encrypt_str: str):
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.key_path, 0, reg.KEY_ALL_ACCESS)
        except FileNotFoundError:
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, self.key_path)
        reg.SetValueEx(key, self.key_name, 0, reg.REG_SZ, encrypt_str)
        reg.CloseKey(key)


if __name__ == '__main__':
    create_default_file('.config')
    # try:
    #     te = EncryptCount('.config', 3, r"Software\MyStock", 'count')
    #     content = te.get_file_content()
    #     te.update_file(content)
    # except FileNotFoundError as e:
    #     print(f'缺少相关配置文件，请联系相关人员')
    #     sys.exit(1)
