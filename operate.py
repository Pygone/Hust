import re
import time

from LoginSession import LoginSession
from Operation.hard_working import hardWorking
from Operation.badminton import Badminton
from Operation.course import Course
from Operation.CourseSelector import CourseSelector
from Operation.professionalCourse import ProfessionalCourse
from Operation.publicCourse import PublicCourse
from Operation.transcript import Transcript


class Operator:
    def __init__(self, login_session: LoginSession, user_id: str):
        self.user_id = user_id
        self.login_session = login_session

    def course(self, course: dict, time_: str = ""):
        resp = self.login_session.get(
            "http://wsxk.hust.edu.cn/hustpass_2.jsp"
        )
        # 获取cookies 中的JSESSIONID
        cookies = self.login_session.cookies
        JSESSIONID = cookies.get("JSESSIONID", domain="wsxk.hust.edu.cn", path="/")
        code = cookies.get(
            "BIGipServerpool-hub-wsxkxt", domain="wsxk.hust.edu.cn", path="/"
        )
        cookies = {"JSESSIONID": JSESSIONID, "BIGipServerpool-hub-wsxkxt": code}
        course = CourseSelector(
            self.user_id,
            course,
            cookies=cookies,
        )
        course.run(time_)

    def transcript(self, query: str = None) -> dict:
        transcript = Transcript(self.login_session, query)
        return transcript.run()

    def get_schedule(self):
        return Course(self.login_session).get_courses()

    def badminton(
            self, date: str, start_time: str, court: dict, partner: dict
    ) -> str:
        badminton = Badminton(self.login_session, date, start_time, court, partner)
        return badminton.run()

    def school_card(self, val: int, password: str) -> str:
        res = self.login_session.get(
            "http://ecard.m.hust.edu.cn/wechat-web/ChZhController/ChongZhiurl.html"
        )
        cardno = re.search('id="cardno" value="(.*)"/>', res.text).group(1)
        res = self.login_session.post(
            "http://ecard.m.hust.edu.cn/wechat-web/ChZhController/ChongZhi.html",
            data={
                "jsoncallback": "jsonp" + str(int(time.time() * 1000)),
                "value": str(val) + "," + str(password),
                "cardno": cardno,
                "acctype": "1",
            },
        )
        return re.search('"errmsg":"(.*?)"', res.text).group(1)

    def professional_credit(self):
        return ProfessionalCourse(self.login_session)

    def public_course(self, query: list):
        worker = PublicCourse(self.login_session, query)
        worker.run()

    def hard_workding(self):
        worker = hardWorking(self.login_session)
        worker.run()
