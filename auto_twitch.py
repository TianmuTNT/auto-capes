from patchright.sync_api import sync_playwright
from threading import Thread, current_thread
from random import choices
from string import ascii_letters, digits
from poplib import POP3_SSL
from email import message_from_bytes
from time import sleep

num_threads = 5

def generate():
    return "".join(choices(ascii_letters + digits, k=10))

def get_code(g, num, time=30):
    host = "pop.yourmail.com"
    port = 995
    username = "yourname@yourmail.com"
    password = "yourpassword"
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
    time -= 1
    if time == 0:
        raise TimeoutError("Get captcha code timeout")
    else:
        sleep(1)
        return get_code(g, num, time)

def get_cape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome", args=["--mute-audio"])
        while True:
            try:
                context = browser.new_context(no_viewport=True)
                page = context.new_page()
                page.goto("https://www.twitch.tv/mrhugo")
                page.wait_for_load_state("domcontentloaded", timeout=50000)

                page.locator("[data-a-target='signup-button']").click()
                g = generate()
                print(f"({current_thread().name}) Name: {g}")
                page.locator("[id='signup-username']").fill(g)
                page.locator("[id='password-input']").fill(g)
                page.locator("xpath=/html/body/div[3]/div/div/div/div/div/div[1]/div/div/div/div[2]/form/div/div[3]/div/div[2]/div[1]/div/select").select_option("2000")
                page.locator("[data-a-target='birthday-month-select']").select_option("1")
                page.locator("[data-a-target='birthday-date-input']").select_option("1")
                page.locator("[data-a-target='signup-phone-email-toggle']").click()
                page.locator("[id='email-input']").fill(g+"@yourdomain.com")
                page.locator("[data-a-target='passport-signup-button']").click()

                code_input = page.get_by_role("textbox", name="数字 1")
                code_input.wait_for()
                code = get_code(g, num_threads)
                print(f"({current_thread().name}) Captcha code: {code}")
                code_input.fill(code)

                setting_button = page.get_by_role("button", name="设置", exact=True)
                setting_button.wait_for()
                setting_button.click()
                page.locator("[data-a-target='player-settings-menu-item-quality']").click()
                page.locator("xpath=/html/body/div[5]/div/div/div/div/div[1]/div/div/div[3]/div[6]/div/div").click()
                page.get_by_label("静音（m）").first.click()

                page.locator("//*[@id=\"root\"]/div/div[1]/nav/div/div[3]/div[3]/div/div[2]/div/div[1]/div/button").click(timeout=50000)
                code_text = page.locator("#root a").filter(has_text="您获得了一份 Mojang 的奖励：Home Cape")
                code_text.wait_for(timeout=300000)
                redeem_code = code_text.text_content().split("换：")[1].split("。")[0]
                print(f"({current_thread().name}) Redeem code: {redeem_code}")
                with open("redeem_codes.txt", "a") as f:
                    f.write(redeem_code + "\n")
                    f.close()
            except Exception as e:
                print(f"({current_thread().name}) ERROR: {e}")
            finally:
                context.close()

if __name__ == "__main__":
    threads = []

    for i in range(num_threads):
        thread = Thread(target=get_cape, name=f"{i+1}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
