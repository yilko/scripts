# aes最常用ECB和CBC模式，ECB模式不需要iv偏移量参数，而CBC需要所以安全性更好
# 以下以CBC模式，nopadding填充来举例
import base64
from Crypto.Cipher import AES


# aes固定是128比特，16字节，先判断明文16字节倍数的范围，然后再用字节0补齐到16倍数
# 目前这里只支持1-240，足够用了，如果还要更长在len_ls改变长度即可
def padding_bytes(content: str, charset: str):
    len_ls = [i for i in range(16, 256, 16)];
    for pwd_len in len_ls:
        # 循环判断长度属于哪个16倍数
        if len(content) > pwd_len:
            continue;
        else:
            # 小于等于某个16倍数时开始转为byte类型并且补充字节0
            pad_content = content.encode(charset);
            # print(len(pad_content), pwd_len);
            if len(content) < pwd_len:
                for i in range(0, pwd_len - len(content)):
                    pad_content += b'\x00';
            return pad_content;


# aes-cbc模式加密
def aes_cbc_encode(key: str, iv: str, content: str, charset: str):
    # 1.明文补齐零并且转为byte类型
    pad_byte = padding_bytes(content, charset);
    # 2.创建aes-cbc对象，aes接收的参数都是bytes类型，需要encode转类型
    aes = AES.new(key.encode(charset), AES.MODE_CBC, iv.encode(charset));
    # 3.aes加密
    aes_byte = aes.encrypt(pad_byte);
    # 4.base64加密
    base64_byte = base64.b64encode(aes_byte);
    # 5.base64转为字符串类型
    done_str = base64_byte.decode(charset);
    return done_str;


# 解密时需要把添加的0去除掉
def remove_padding(content: bytes):
    return content.rstrip(b"\x00") if content[-1] == 0 else content;


# aes-cbc模式解密
def aes_cbc_decode(key: str, iv: str, content: str, charset: str):
    # 1.加密后的字符串转为byte类型
    encode_byte = content.encode(charset);
    # 2.进行base64解密
    base64_byte = base64.b64decode(encode_byte);
    # 3.创建aes-cbc对象，并把参数从字符串转为bytes类型
    aes = AES.new(key.encode(charset), AES.MODE_CBC, iv.encode(charset));
    # 4.aes解密
    aes_byte = aes.decrypt(base64_byte);
    # 5.aes去除byte类型明文补充的0
    origin_byte = remove_padding(aes_byte);
    # 6.aes明文从byte类型转为字符串
    origin_str = origin_byte.decode(charset);
    return origin_str;


if __name__ == '__main__':
    # key和iv必须要16个字节数据或者是16倍数
    key, iv, content, charset = "yilko_aespwd_key", "yilko_aespwd_kiv", "yilko_20241030_000000_0", "utf-8";
    encode_content = aes_cbc_encode(key, iv, content, charset);
    print(encode_content);
    oringin_content = aes_cbc_decode(key, iv, encode_content, charset);
    print(oringin_content);
