import requests
import json
import time
import logging
import base64
import os
from dotenv import load_dotenv
from utils import rm_transparent, ocr_image

# ===== 加载环境变量 =====
load_dotenv()

BASE_URL = "https://www.mhh1.com/"
COOKIE_FILE = "cookies.json"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
PUSH_URL = os.getenv("PUSH_URL")

# ===== 日志配置 =====
logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


class SignClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "referer": "https://www.mhh1.com",
        }
        self.load_cookie()

    def init_session(self):
        logging.info("初始化会话（访问首页）")
        self.session.get(BASE_URL, headers=self.headers)

    def load_cookie(self):
        try:
            with open(COOKIE_FILE, "r") as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
                logging.info("加载cookie成功")
                return True
        except:
            logging.info("无cookie文件，准备登录")
            return False

    def save_cookie(self):
        with open(COOKIE_FILE, "w") as f:
            json.dump(self.session.cookies.get_dict(), f)

    def get_nonce(self):
        url = BASE_URL + "/wp-admin/admin-ajax.php?action=285d6af5ed069e78e04b2d054182dcb5"

        r = self.session.get(url, headers=self.headers)

        print("状态码:", r.status_code)
        print("返回内容:", r.text[:200])  # 只看前200字符

        return r.json()["_nonce"], int(r.json()["user"]["id"]) != 0

    def get_captcha(self, nonce):
        url = BASE_URL + f"/wp-admin/admin-ajax.php?_nonce={nonce}&action=b9215121b88d889ea28808c5adabbbf5&type=getCaptcha"
        r = self.session.get(url, headers=self.headers).json()
        return r["data"]["imgData"]

    def login(self, nonce):
        logging.info("开始登录")

        img_base64 = self.get_captcha(nonce)
        img_bytes = base64.b64decode(img_base64[22:])
        img_bytes = rm_transparent(img_bytes)

        captcha = ocr_image(img_bytes)
        logging.info(f"验证码识别: {captcha}")

        if not captcha or len(captcha) < 3:
            raise Exception("验证码识别失败")

        login_url = BASE_URL + f"/wp-admin/admin-ajax.php?_nonce={nonce}&action=0ac2206cd584f32fba03df08b4123264&type=login"

        data = {
            "username": USERNAME,
            "password": PASSWORD,
            "captcha": captcha
        }

        r = self.session.post(login_url, data=data, headers=self.headers)

        if "success" in r.text.lower():
            logging.info("登录成功")
            self.save_cookie()
            return True
        else:
            logging.error(f"登录失败: {r.text}")
            return False

    def sign(self, nonce):
        url = BASE_URL + f"/wp-admin/admin-ajax.php?_nonce={nonce}&action=bfabd9151866d43ef3cb467ca6a0473c&type=goSign"
        r = self.session.get(url, headers=self.headers).json()
        msg = r.get("msg", "未知结果")
        logging.info(f"签到结果: {msg}")
        return msg

    def push(self, msg):
        try:
            requests.post(PUSH_URL, data={"title": msg})
        except:
            logging.error("推送失败")

    def run(self):
        self.init_session()

        has_cookie = self.load_cookie()

        for i in range(3):
            try:
                nonce, logged = self.get_nonce()

                #  关键逻辑
                if not logged:
                    logging.info("未登录，开始登录流程")

                    if not self.login(nonce):
                        continue

                    # 登录后重新获取 nonce
                    nonce, logged = self.get_nonce()

                    if not logged:
                        raise Exception("登录后仍未登录成功")

                #  已登录 → 签到
                msg = self.sign(nonce)
                self.push(msg)
                return

            except Exception as e:
                logging.error(f"第{i + 1}次失败: {e}")
                time.sleep(2)

        logging.error("多次失败，程序退出")


if __name__ == "__main__":
    SignClient().run()