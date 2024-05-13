import os
import json
import subprocess
import platform

# 检查xray是否已安装
def check_xray_installed():
    try:
        subprocess.check_output(['xray', '-version'])
        return True
    except FileNotFoundError:
        return False

def check_warp_installed():
    try:
        subprocess.check_output(['warp-cli', '-V'])
        return True
    except FileNotFoundError:
        return False


# 安装cloudflare warp
def install_warp():
    os_release = platform.freedesktop_os_release()["NAME"]
    if os_release.lower() == "ubuntu":
        os.system(
            "curl https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg")
        os.system(
            'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list')
        os.system("sudo apt update")
    elif os_release.lower() == "debian":
        os.system(
            "curl https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg")
        os.system(
            'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list')
        os.system("sudo apt update")
    else:
        os.system("sudo rpm -ivh https://pkg.cloudflareclient.com/cloudflare-release-el8.rpm")

    os.system("apt install cloudflare-warp")
    os.system("warp-cli register")
    os.system("warp-cli set-mode proxy")


# 读取config.json文件
def read_config():
    with open('/usr/local/etc/xray/config.json', 'r') as f:
        config = json.load(f)
    return config

# 修改config.json文件
def modify_config(config):
    # 如果routing不存在，则创建routing对象，并向rules数组插入一个对象
    print("start update config file......")
    if 'routing' not in config:
        config['routing'] = {
            'domainStrategy': 'AsIs',
            'rules': [
                {
                    'type': 'field',
                    'domain': ['openai.com', 'ai.com', 'chatgpt.com'],
                    'outboundTag': 'WARP'
                }
            ]
        }
    # 如果routing存在，但没有domainStrategy，就添加domainStrategy
    elif 'domainStrategy' not in config['routing']:
        config['routing']['domainStrategy'] = 'AsIs'

    if 'rules' in config['routing']:
        config['routing']['rules'].append(
            {
                'type': 'field',
                'domain': ['openai.com', 'ai.com'],
                'outboundTag': 'WARP'
            }
        )

    # 向outbounds数组插入一个对象
    has_warp = False
    outbounds = config['outbounds']
    for item in outbounds:
        if 'tag' in item and item['tag'] == 'WARP':
            has_warp = True

    if not has_warp:
        config['outbounds'].append({
            'tag': 'WARP',
            'protocol': 'socks',
            'settings': {
                'servers': [
                    {
                        'address': '127.0.0.1',
                        'port': 40000
                    }
                ]
            }
        })
    # 保存修改后的config.json文件
    with open('/usr/local/etc/xray/config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print('update config success！')

# 重启xray
def restart_xray():
    print("restarting xray......")
    subprocess.run(['systemctl', 'restart', 'xray'])
    print("restart success！")

# 执行操作
print('check installed xray......')
if not check_xray_installed():
    print('no xray found!')
else:
    print("check installed warp......")
    if not check_warp_installed():
        print("start install warp......")
        install_warp()
    print("warp install success!")

    os.system("warp-cli connect")

    print("check chat.openai.com......")
    if 0 == os.system("curl chat.openai.com --proxy socks5://127.0.0.1:40000"):
        print("chat.openai.com connect success！")

    config = read_config()
    modify_config(config)
    restart_xray()


