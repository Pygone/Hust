import datetime
import json
import re
import time

from bs4 import BeautifulSoup

from LoginSession import LoginSession


class Badminton:
    def __init__(self, session: LoginSession, date: str, start_time: str, court: dict, partner: dict):
        self.session = session
        self.date = date
        self.start_time = datetime.datetime.strptime(start_time, "%H").strftime("%H:%M:%S")
        self.end_time = (
                datetime.datetime.strptime(self.start_time, "%H:%M:%S") + datetime.timedelta(hours=2)).strftime(
            "%H:%M:%S")
        self.partner = partner
        self.cg_csrf_token = None
        self.partners = None
        with open("src/court.json") as f:
            info = json.load(f)
            self.court_cdbh = info[court["name"]]["cdbh"]
            self.court_number = info[court["name"]]["number"][court["number"]]

    def ecard(self):
        url = "http://ecard.m.hust.edu.cn/wechat-web/service/new_profile.html"
        res = self.session.get(url)
        soup = BeautifulSoup(res.text, features="html.parser")
        bills = float(soup.section.find_all("dl")[9].dd.div.span.string.strip("元"))
        return bills < 40 if self.start_time >= "18:00:00" else bills < 20

    def get_partner(self, text):
        params = {
            "id": "0",
            "member_id": "56558",
            "partner_name": "",
            "partner_type": "1",
            "partner_schoolno": "",
            "partner_passwd": "",
            "cg_csrf_token": self.cg_csrf_token,
        }
        if self.partner is None:
            self.partners = re.findall("putPartner\('(.*)','(.*)','(.*)','1'\);", text)
            for partner in self.partners:
                if partner[2] != self.session.userId:
                    params["partner_name"] = partner[1]
                    params["partner_schoolno"] = partner[2]
                    params["partner_passwd"] = partner[0]
                    text_ = self.session.post("http://pecg.hust.edu.cn/cggl/front/addPartner", data=params).text
                    info = re.search(r"alert\(HTMLDecode\('(.*)'\), '提示信息'\);", text_).group(1)
                    if "你已添加该同伴，请勿重复添加" in info:
                        self.partner = {
                            "name": partner[1],
                            "ID": partner[2],
                            "passwd": partner[0],
                        }
                        break

    def run(self) -> str:
        # if self.ecard():
        #     return "电子账户余额不足"
        self.session.headers["Referer"] = str(self.session.get("http://pecg.hust.edu.cn/cggl/index1").url)
        text = self.session.get("http://pecg.hust.edu.cn/cggl/index1").text
        self.cg_csrf_token = re.search('name="cg_csrf_token" value="(.*)" />', text).group(1)

        yesterday = (datetime.datetime.strptime(self.date, "%Y-%m-%d")) - datetime.timedelta(days=1)
        url = f"http://pecg.hust.edu.cn/cggl/front/syqk?date={yesterday.strftime('%Y-%m-%d')}&type=1&cdbh=45"
        text = self.session.get(url).text
        self.get_partner(text)

        params = [
            ("starttime", self.start_time),  # 开始时间
            ("endtime", self.end_time),  # 结束时间
            ("partnerCardType", "1"),  # 第一个类型:学生
            ("partnerName", self.partner["name"]),  # 同伴姓名
            ("partnerSchoolNo", self.partner["ID"]),  # 同伴学号
            ("partnerPwd", self.partner["password"]),  # 同伴密码
            ("choosetime", self.court_number),  # 此处设置场地号
            ("changdibh", self.court_cdbh),  # 此处设置场地 光谷体育馆,西边体育馆,游泳馆
            ("date", self.date),  # 预约日期
            ("cg_csrf_token", self.cg_csrf_token),
        ]
        wait = str(datetime.datetime.strptime(self.date + " 08", "%Y-%m-%d %H") - datetime.timedelta(days=2))
        wait = time.mktime(time.strptime(wait, "%Y-%m-%d %H:%M:%S"))
        while time.time() - wait < 0:
            time.sleep(1)
        text = self.session.post("http://pecg.hust.edu.cn/cggl/front/step2", params=params).text
        try:
            data = re.search('name="data" value="(.*)" type', text).group(1)
            Id = re.search('name="id" value="(.*)" type', text).group(1)
            params = [
                ("data", data),
                ("id", Id),
                ("cg_csrf_token", self.cg_csrf_token),
                ("select_pay_type", -1),
            ]
            text = self.session.post("http://pecg.hust.edu.cn/cggl/front/step3", params=params).text
        except AttributeError:
            return re.search(r"alert\(HTMLDecode\('(.*)'\), '提示信息'\);", text).group(1)
        return re.search(r"alert\(HTMLDecode\('(.*)'\), '提示信息'\);", text).group(1)
