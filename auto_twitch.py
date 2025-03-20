from patchright.sync_api import sync_playwright
from threading import Thread, current_thread
from random import choices
from string import ascii_letters, digits
from poplib import POP3_SSL
from email import message_from_bytes

num_threads = 3

def generate():
    return "".join(choices(ascii_letters + digits, k=10))

def get_code(g, num):
    host = "pop.xxx.com"
    port = 995
    username = "xxx@yourmail.com"
    password = "xxx"
    pop_server = POP3_SSL(host, port)
    pop_server.user(username)
    pop_server.pass_(password)
    count, _ = pop_server.stat()
    start = count
    end = max(1, count - (num - 1))
    for i in range(start, end - 1, -1):
        try:
            response, msg_lines, _ = pop_server.retr(i)
            msg_raw = b'\n'.join(msg_lines)
            email_message = message_from_bytes(msg_raw)
            if email_message and email_message.get('To', '').split("@")[0] == g:
                code = email_message.get('Subject').split("?")[3].split("_")[0]
                pop_server.quit()
                return code
        except Exception:
            continue
    pop_server.quit()
    return get_code(g, num)

def get_cape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        while True:
            try:
                context = browser.new_context(no_viewport=True)
                page = context.new_page()
                page.goto("https://www.twitch.tv/mrhugo")
                page.wait_for_load_state("domcontentloaded", timeout=50000)

                page.locator("[data-a-target='signup-button']").click()
                g = generate()
                page.locator("[id='signup-username']").fill(g)
                page.locator("[id='password-input']").fill(g)
                page.locator("xpath=/html/body/div[3]/div/div/div/div/div/div[1]/div/div/div/div[2]/form/div/div[3]/div/div[2]/div[1]/div/select").select_option("2000")
                page.locator("[data-a-target='birthday-month-select']").select_option("1")
                page.locator("[data-a-target='birthday-date-input']").select_option("1")
                page.locator("[data-a-target='signup-phone-email-toggle']").click()
                page.locator("[id='email-input']").fill(g+"@yourdomain.com")
                page.locator("[data-a-target='passport-signup-button']").click()

                code = get_code(g, num_threads)
                print(f"({current_thread().name}) {code}")
                page.get_by_role("textbox", name="数字 1").fill(code)

                setting_button = page.get_by_role("button", name="设置", exact=True)
                setting_button.wait_for()
                setting_button.click()
                page.locator("[data-a-target='player-settings-menu-item-quality']").click()
                page.locator("xpath=/html/body/div[5]/div/div/div/div/div[1]/div/div/div[3]/div[5]/div/div/div/div/label").click()
                page.get_by_label("静音（m）").first.click()

                page.locator("//*[@id=\"root\"]/div/div[1]/nav/div/div[3]/div[3]/div/div[2]/div/div[1]/div/button").click(timeout=50000)
                code_text = page.locator("#root a").filter(has_text="您获得了一份 Mojang 的奖励：Home Cape")
                code_text.wait_for(timeout=300000)
                redeem_code = code_text.text_content().split("换：")[1].split("。")[0]
                print(f"({current_thread().name}) {redeem_code}")
                with open("redeem_codes.txt", "a") as f:
                    f.write(redeem_code + "\n")
                    f.close()
            except Exception as e:
                print(f"({current_thread().name}) {e}")
            finally:
                context.close()

if __name__ == "__main__":
    threads = []

    for i in range(num_threads):
        thread = Thread(target=get_cape, name=f"{i+1:03d}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
