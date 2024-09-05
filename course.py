# 请在校园网环境使用，适用于研究生课程补退改选捡漏
import selenium
import time
import datetime
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from selenium.webdriver.chrome.options import Options

all_todo = []
username = ""
password = ""
campus = ""
use_campus_filter = True
use_course_filter = True
sso = ""
course_page = ""
use_log = True
sleep_time_after_confirm = 5
sleep_time_after_refresh = 0.5
page_alive_time = 60
use_headless = True
xpaths = {}
start_time = datetime.datetime.now()


def create_log_file():
    if use_log:
        with open('log.txt', 'w') as log_file:
            log_file.write('-------------------------------' + datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S') + '-------------------------------\n\n')


def write_log(log):
    if use_log:
        with open('log.txt', 'a') as log_file:
            log_file.write(log + '\n\n')


def read_config():
    global all_todo, username, password, campus, use_campus_filter, use_course_filter, sso, course_page, use_log, \
        sleep_time_after_confirm, sleep_time_after_refresh, page_alive_time, use_headless, xpaths
    try:
        with open('config.json', 'r', encoding="utf-8") as config_file:
            config_data = json.load(config_file)
            all_todo = config_data["all_todo"]
            username = config_data["username"]
            password = config_data["password"]
            campus = config_data["campus"]
            use_campus_filter = config_data["use_campus_filter"]
            use_course_filter = config_data["use_course_filter"]
            sso = config_data["sso"]
            course_page = config_data["course_page"]
            use_log = config_data["use_log"]
            sleep_time_after_confirm = config_data["sleep_time_after_confirm"]
            sleep_time_after_refresh = config_data["sleep_time_after_refresh"]
            page_alive_time = config_data["page_alive_time"]
            use_headless = config_data["use_headless"]
            xpaths = config_data["xpaths"]

    except Exception as e:
        print(e)
        write_log(str(e))
        exit(-1)


def check_refresh():
    global start_time
    # 定期刷新整个界面
    time_now = datetime.datetime.now()
    if (time_now - start_time).seconds > page_alive_time:
        return True
    return False


def deal_part(browser, part):
    # 来到对应的课程板块
    browser.find_element(by=By.XPATH, value=part["base_path"]).click()
    if part["have_second_path"] and len(part["second_path"]) > 0:
        browser.find_element(by=By.XPATH,
                             value=part["second_path"]).click()

    if use_campus_filter and not part["have_second_path"]:  # 二级页面没有校区筛选
        select_element_campus = browser.find_element(By.ID, 'fankc_xq')
        select_campus = Select(select_element_campus)
        select_campus.select_by_visible_text(campus)

    if use_course_filter:
        if part["have_second_path"]:
            select_element_course = browser.find_element(By.ID, 'fakzkc_sfym')
        else:
            select_element_course = browser.find_element(By.ID, 'fankc_sfym')
        select_course = Select(select_element_course)
        select_course.select_by_visible_text("未满")

    # 界面内刷新
    browser.find_element(By.ID, part["refresh_btn_id"]).click()
    time.sleep(sleep_time_after_refresh)

    # 匹配所有选课button
    all_btn = browser.find_elements(by=By.CLASS_NAME, value=part["xk_btn_class_name"])

    # 匹配所有课程信息
    tables = browser.find_elements(By.TAG_NAME, 'table')
    datas = []
    for table in tables:
        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            # 获取每行的文本内容
            cols = row.find_elements(By.TAG_NAME, 'td')
            data = [col.text for col in cols]

            datas.append(data)

    write_log("got data:\n" + str(datas))
    datas = datas[1:]  # 删除匹配到的标题行
    if part["have_second_path"]:  # 删除匹配到的一级列表的选课button
        for i in range(0, len(datas)):
            if not datas[i]:
                datas = datas[i + 1:]
                all_btn = all_btn[i:]
                break

    for i in range(0, len(datas)):
        mdata = datas[i]
        if mdata:
            for j in all_todo:
                if mdata[0] == j:  # 此处也可以使用更多信息进行匹配
                    all_btn[i].click()
                    browser.find_element(by=By.XPATH,
                                         value=xpaths["select_confirm_xpath"]).click()
                    time.sleep(sleep_time_after_confirm)
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "   tried    " + j)
                    write_log(
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "    tried    " + j)
    if part["have_second_path"]:  # 关闭二级列表
        browser.find_element(By.CLASS_NAME, part["close_class_name"]).click()


def course_grab():
    global all_todo, username, password, campus, use_campus_filter, use_course_filter, sso, course_page, \
        sleep_time_after_confirm, sleep_time_after_refresh, page_alive_time, use_headless, xpaths, start_time
    chrome_options = Options()
    if use_headless:
        chrome_options.add_argument('--headless')
    browser = selenium.webdriver.Chrome(options=chrome_options)
    while True:
        try:
            browser.get(sso)
            start_time = datetime.datetime.now()
            if browser.title == "统一身份认证":
                browser.switch_to.frame("loginIframe")
                username_element = browser.find_element(by=By.XPATH, value=xpaths["username_element_xpath"])
                password_element = browser.find_element(by=By.XPATH, value=xpaths["password_element_xpath"])
                username_element.send_keys(username)
                password_element.send_keys(password)
                confirm = browser.find_element(by=By.XPATH,
                                               value=xpaths["login_confirm_xpath"])
                confirm.click()
                browser.switch_to.default_content()
                print("login success")
                write_log("login success")
            else:
                browser.get(course_page)
                time.sleep(0.2)
                while True:
                    need_refresh = check_refresh()
                    if need_refresh:
                        break
                    # 对每个板块进行课程搜索
                    course_part_xpath = xpaths["course_part_xpath"]
                    for part in course_part_xpath:
                        deal_part(browser=browser, part=part)

        except Exception as e:
            print(e)
            write_log(str(e))


if __name__ == '__main__':
    read_config()
    create_log_file()
    course_grab()
