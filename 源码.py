import random
import string
import keyboard
import time

def random_8():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

print('脚本已启动，按 F8 停止。')
while True:
    if keyboard.is_pressed('f8'):          # 检测到 F8 立即退出
        print('F8 被按下，脚本结束。')
        break

    s = random_8()
    keyboard.write(s)                      # 输出 8 位随机串
    keyboard.send('enter')                 # 按回车
    time.sleep(0.1)                        # 可调整频率
