import time
import pandas as pd
import pywinauto
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from playwright.sync_api import sync_playwright
from collections import Counter
from pywinauto.application import Application

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']


def main():
    with sync_playwright() as p:
        # open canvas page
        #browser = p.chromium.launch(headless=False)
        context = p.chromium.launch_persistent_context(user_data_dir='/path/to/user/data/directory',headless=False)
        page = context.new_page()
        page.goto(url)
        # login canvas
        page.fill("//*[@id='pseudonym_session_unique_id']",USERNAME)
        page.fill("//*[@id='pseudonym_session_password']",PASSWORD)
        #page.locator('button:text("Log In")').click()
        #using this instead cause they wanted to change the button type for some reason
        page.click("//*[@id='login_form']/div[4]/div[2]/button")


        # opens zoom link depending on number of diff meetings, relies on amount of links in
        # the iframe, may break one day if zoom layout changes
        page.wait_for_load_state("networkidle")
        frame1 = page.frame('tool_content')
        locatorlist = frame1.get_by_role('link').all()
        if len(locatorlist) > 1:
            count = -1
            for meeting_locator in locatorlist:
                x = meeting_locator.get_attribute('href')
                count += 1
                if df2['meeting_id'].iloc[0] in x:
                    locator = locatorlist[count]
                    print(locator)
                    break
        else: 
            locator = frame1.get_by_role('link')     
        
      
        with page.expect_popup() as popup_info:
            locator.click()
        popup = popup_info.value

        #do something like if page is launch meeting page, close browser
        
        popup.wait_for_timeout(4000)
        testlocatorText = popup.get_by_role('button').all_inner_texts()

        if "Launch Meeting" in testlocatorText:
            page.close()
            popup.close()

        elif "Launch Meeting" not in testlocatorText:
            print(popup.url)
            print('login required')
            popup.get_by_placeholder("User Name").fill(USERNAME)
            popup.get_by_placeholder("Password").fill(PASSWORD)
            popup.get_by_role("button",name="Sign in").click()
            with page.expect_popup() as popup_info:
                locator.click()
            popup = popup_info.value
            popup.wait_for_timeout(4000)
            testlocatorText = popup.get_by_role('button').all_inner_texts()
            page.close()
            popup.close()

        #page.close()

def zoom_window():
    # connect to zoom app
    app = Application(backend='uia').connect(title="Zoom Meeting",timeout=5)
    if app.ThisMeetingisbeingrecordedbythehostoraparticipant.exists(timeout=3,retry_interval=None) is True:
        app.ThisMeetingisbeingrecordedbythehostoraparticipant.child_window(title="Got It", control_type="Button").click_input()

    window = app.ZoomMeeting.child_window(title="ContentLeftPanel", control_type="Window").wrapper_object()
    window.click_input()
    app.ZoomMeeting.child_window(title="View", control_type="Button").click_input()
    #if 'Exit Full Screen' in pywinauto.findwindows.find_elements(control_type='MenuItem'):
    app.ZoomMeeting.child_window(title="Exit Full Screen", control_type="MenuItem").click_input()

    # open chat
    chatButton = app.ZoomMeeting.child_window(title="Open Chat Panel, Alt+H", control_type="Button")
    chatButton.click()

    # chat list
    chatBox = app.ZoomMeeting.child_window(title="chat text", control_type="List").wrapper_object()
    chat_message = app.ZoomMeeting.child_window(title="Input chat text Type message here…", control_type="Edit")
    chat_button = app.ZoomMeeting.child_window(title="Send message Press Arrow Left and Right for more message composition options", control_type="Button")
    #app.ZoomMeeting.print_control_identifiers()

    i=-1
    chat_list = [None]*10
    chat_list_old = []
    message_old = None
    while True:
        c=Counter()
        for chat_message in chatBox:
            chat_entry = str(chatBox.get_item(i))
            chat_entry = chat_entry.split(',',maxsplit=2)[2]
            chat_entry = chat_entry.rsplit(',',maxsplit=3)[0]
            print(chat_entry)
            #chat_entry = chat_entry[:-1]
            chat_list[-i] = chat_entry
            c[chat_entry] += 1
            i-=1
            if i ==-10:
                break

        for k,v in c.items():
            if message_old == k:
                continue
            if chat_list_old == chat_list:
                print("duplicate list")
                continue
            if v>=5:
                print("This will send message >> ",k)
                chat_message.type_keys(k.lstrip(),with_spaces=True)
                chat_button.click()
                #time.sleep(10)
                message_old = k 
                break
            
        i=-1
        chat_list_old = chat_list
        chat_list = [None]*10
        time.sleep(1)

df = pd.read_csv("datetime_zoom.csv")
df = df.fillna(0).astype({'meeting_id':'int64'})
df = df.astype({'meeting_id':'str'})
launched = False

#launches canvas when lesson time in csv == current time
while True:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    #test = "26/01/2023 12:00"
    df2=df[df['datetime'].isin([now])]
    if not df2.empty and launched ==False:
        launched = True
        url = df2['url'].iloc[0]
        main()
        time.sleep(3)
        zoom_window()
        