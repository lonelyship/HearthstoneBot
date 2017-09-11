# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import sys
import requests
import json
import os
import logging
import configparser
from logging import handlers
import traceback
import datetime
import time
import uuid
import pymysql.cursors
import threading
from urllib.parse import quote, urlencode

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, URITemplateAction, PostbackTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent, ImagemapSendMessage, BaseSize, URIImagemapAction,
    ImagemapArea, MessageImagemapAction, ImageSendMessage,
)


def initial_log(file_name):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("MaGa_Line_GW")
    log_filename = os.path.join('log', file_name)
    log_handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=300000, backupCount=5, )
    log_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger


logger = initial_log('gw_log.txt')
global_locker = threading.Lock()
config_filename = os.path.join('config', 'Setting.ini')


class LineGW:
    def __init__(self, port):
        global logger
        logger.info("Start server {0} port ".format(port))
        config = configparser.ConfigParser()
        config.read(config_filename, encoding="utf-8-sig")  # ,encoding="utf-8"
        line_channel_secret = config["SETTING"]["LINE_CHANNEL_SECRET"]
        line_channel_access_token = config["SETTING"]["LINE_CHANNEL_ACCESS_TOKEN"]
        # self.api_url = config["SETTING"]["ROBO_URL"]
        self.line_bot_api = LineBotApi(line_channel_access_token)
        self.handler = WebhookHandler(line_channel_secret)
        self.group_keyword = "小花"
        # self.db_connect_host = config["DB"]["HOST"]
        # self.db_connect_name = config["DB"]["NAME"]
        # self.db_connect_password = config["DB"]["PASSWORD"]
        # self.db_connect_db = config["DB"]["DB"]

        # self.conn = self.connect_db()
        # c = self.conn.cursor()
        self.port = port
        self.application = Flask(__name__)
        app = self.application
        handler = self.handler

        @app.route('/gw/linecallback', methods=['GET'])
        def verify():
            return 'OK', 200



        @app.route("/gw/linecallback", methods=['POST'])
        def callback():
            # get X-Line-Signature header value
            signature = request.headers['X-Line-Signature']
            logger.info("{0} Port get data".format(port))
            body = request.get_data(as_text=True)
            # get request body as text
            logger.info("Request body: " + body)
            # handle webhook body
            try:
                handler.handle(body, signature)
            except InvalidSignatureError:
                abort(400)

            return 'OK', 200

        @handler.add(FollowEvent)
        def handle_follow(event):
            line_id = event.source.user_id
            # self.search_room_id(line_id)

        @handler.add(JoinEvent)
        def handle_join(event):
            line_id = event.source.group_id
            # self.search_room_id(line_id)

        @handler.add(MessageEvent, message=TextMessage)
        def handle_message(event):
            text = event.message.text
            send_text = True
            check_user = True
            if text.startswith("@"):
                text= text.replace("@","")
            elif text.startswith("＠"):
                text= text.replace("＠","")
            else:
                return
            # if isinstance(event.source, SourceUser):
            #     im_id = event.source.user_id
            # if isinstance(event.source, SourceGroup):
            #     im_id = event.source.group_id
            #     check_user = False
            #     if self.group_keyword == text[0:2]:
            #         text = text[2:]
            #     else:
            #         send_text = False
            # if isinstance(event.source, SourceRoom):
            #     im_id = event.source.room_id
            #     check_user = False
            #     if self.group_keyword == text[0:2]:
            #         text = text[2:]
            #     else:
            #         send_text = False
            #
            # if text in line_key_word:
            #     key_contain = ""
            #     for contain in line_key_word_all:
            #         account_bind = check_account_bind(im_id)
            #         if text == contain["KeyWord"]:
            #             contain_bind = int(contain["checkbind"])
            #             if contain_bind == 0:
            #                 key_contain = contain["Content"]
            #             else:
            #                 if account_bind == 0:
            #                     key_contain = {"Type": "textMessage", "text": "您尚未綁定，無法使用此功能，請透過「個人化服務」進行綁定。", "url_key": "A"}
            #                 else:
            #                     key_contain = contain["Content"]
            #     send_line_test_message(event.reply_token, im_id, key_contain)
            #
            # elif text in action_word:
            #     action_contain = ""
            #     for contain in action_word_all:
            #         if text == contain["KeyWord"]:
            #             action_contain = contain["Content"]
            #             action_typ = contain["Content"]["url_key"]
            #
            #             self.write_user_history('IC', action_typ, im_id)
            #     action_word_message(event.reply_token, im_id, action_contain)
            #
            # else:
            #     payload = {'Q': text, 'source': 'LINE', 'USER': im_id, 'SID': '0002', 'SKEY': '1234567'}
            #     payload = urlencode(payload, quote_via=quote)
            #     error_time_out = False
            #     error_text = "系統忙碌中.請稍後再試"
            #
            #     if send_text is True:
            #         room_id = self.search_room_id(im_id)
            #         replay_message = []
            #         try:
            #             response = requests.get(self.api_url, params=payload, timeout=4)
            #         except requests.exceptions.Timeout as e:
            #             a = TextSendMessage(text=error_text)
            #             replay_message.append(a)
            #             logger.exception('LineGW exception' + str(e))
            #             error_time_out = True
            #
            #         else:
            #             response.raise_for_status()
            #             response_json = response.json()
            #             for element_data in response_json["ELEMENTS"]:
            #                 json_data = self.line_check_elements_type(element_data, check_user)
            #                 replay_message.append(json_data)
            #             logger.info(replay_message)
            #         finally:
            #             self.write_db(room_id, im_id, text, 1, 1)
            #             try:
            #                 self.line_bot_api.reply_message(event.reply_token, replay_message)
            #             except requests.exceptions.RequestException as e:
            #                 if error_time_out is False:
            #                     for qq in response_json["ELEMENTS"]:
            #                         data_type = qq[0]["TYPE"]
            #                         if data_type == "TEXT":
            #                             response_text = qq[0]["MSG"]
            #                             self.write_db(room_id, "viki", response_text, 1, 0)
            #                         else:
            #                             self.write_db(room_id, "viki", response_text, 100, 0)
            #                 else:
            #                     self.write_db(room_id, "viki", error_text, 1, 0)
            #
            #             else:
            #                 if error_time_out is False:
            #                     for qq in response_json["ELEMENTS"]:
            #                         data_type = qq[0]["TYPE"]
            #                         if data_type == "TEXT":
            #                             response_text = qq[0]["MSG"]
            #                             self.write_db(room_id, "viki", response_text, 1, 1)
            #                         else:
            #                             logger.info(qq[0])
            #
            #                             response_text = str(qq[0])
            #                             self.write_db(room_id, "viki", response_text, 100, 1)
            #                 else:
            #                     self.write_db(room_id, "viki", error_text, 1, 1)


            # https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/瘟疫?locale=zhTW
            url = 'https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/'+text;
            headers = {'X-Mashape-Key': 'zJ6HmBMQfamshXuEdrPbQ9QmIMtrp1yaw7hjsnLY3DeERkqtQI'}
            params = dict(
                locale='zhTW',
            )

            resp = requests.get(url=url, params=params,headers=headers)
            data = json.loads(resp.text)

            count = 0;
            ObjArray=[]
            if len(data) > 0:
                for item in data:
                    if 'img' in item and 'text' in item and 'name' in item:
                        if len(ObjArray) >= 5:
                            break;
                        imgurl = item['img'].replace("http","https")
                        print("!!!!!", imgurl)

                        import re


                        cleanr = re.compile('<.*?>')
                        cleantext = re.sub(cleanr, '', item['text'])
                        cleantext = cleantext.replace('\\n','\n')

                        textObj = TextSendMessage(text=item['name']+"\n"+cleantext)
                        imgObj  = ImageSendMessage(
                                    original_content_url=imgurl,
                                       preview_image_url=imgurl
                                )

                        ObjArray.append(textObj)
                        ObjArray.append(imgObj)
                        count = count + 1
                        break;


                    else:
                        continue;

                if count == 0:
                    text = TextSendMessage(text="查無資料")
                    self.line_bot_api.reply_message(event.reply_token, text)
                else:
                    self.line_bot_api.reply_message(event.reply_token, ObjArray)
                #
                # text = TextSendMessage(text="查無資料")
                # self.line_bot_api.reply_message(event.reply_token, text)




        @handler.add(MessageEvent, message=StickerMessage)
        def handle_sticker_message(event):
            logger.info("Line get sticker :%s Line_id = %s", event.message.sticker_id, event.source.user_id)

            self.line_bot_api.reply_message(
                event.reply_token,
                StickerSendMessage(
                    package_id=event.message.package_id,
                    sticker_id=event.message.sticker_id)
            )

        def check_action(action_content, im_id):
            actions = []
            for single_action in action_content:
                type = single_action["type"]
                label = single_action["text"]
                if type == "url":
                    url = single_action["url"]
                    action = URITemplateAction(label=label, uri=url)
                    actions.append(action)
                if type == "text":
                    action = MessageTemplateAction(
                            label=label,
                            text=label)
                    actions.append(action)
            return actions

        def check_url(urlkey, im_id):
            full_url = ""
            try:
                if self.conn is None:
                    self.conn = self.connect_db()
                if self.conn:
                    c = self.conn.cursor()
                    c.execute("SELECT `id` FROM `member_lineuser` WHERE `SourceID`=%s ", (im_id,))
                    id_data = c.fetchone()
                    source_ID_id = ""
                    if id_data is not None:
                        source_ID_id =id_data["id"]

                full_url = "url_key={url_key}&SourceID={sourceID}&SourceID_id={sourceID_id}&Source_id={Sourceid}&random={random_number}".format(url_key= urlkey,sourceID=im_id,sourceID_id=source_ID_id,Sourceid=self.source,random_number = uuid.uuid4().hex)
                logger.info(full_url)
            except BaseException as e:
                # self.conn_close()
                logger.exception('Other exception' + str(e))
            url = full_url
            return url

        def check_account_bind(user_id):
            account_enable = 0
            try:
                if self.conn is None:
                    self.conn = self.connect_db()
                if self.conn:
                    c = self.conn.cursor()
                    c.execute("SELECT `id` FROM `member_lineuser` WHERE `SourceID`=%s ", (user_id,))
                    id_data = c.fetchone()
                    if id_data is not None:
                        source_id_id = id_data["id"]
                        c.execute("SELECT `Enabled` FROM `member_bind` WHERE `SourceID_id`=%s ",
                                  (source_id_id,))
                        account_id_data = c.fetchone()
                        if account_id_data is not None:
                            account_enable = account_id_data["Enabled"]
            except BaseException as e:
                # self.conn_close()
                logger.exception('Other exception' + str(e))
            return account_enable

        def check_imagemap_action(actions, im_id):
            action_content = []
            for action in actions:
                action_type = action["type"]
                if action_type == "imid_url":
                    url_key = action["url_key"]
                    url = check_url(url_key,im_id)
                    link_uri = action["link_uri"] +url

                    x = action["area"]["x"]
                    y = action["area"]["y"]
                    width = action["area"]["width"]
                    height = action["area"]["height"]
                    action_single = URIImagemapAction(
                        link_uri=link_uri,
                        area=ImagemapArea(x=x, y=y, width=width, height=height), )
                    action_content.append(action_single)
                elif action_type == "one_imid_url":
                    link_uri = action["link_uri"]+im_id
                    x = action["area"]["x"]
                    y = action["area"]["y"]
                    width = action["area"]["width"]
                    height = action["area"]["height"]
                    action_single = URIImagemapAction(
                        link_uri=link_uri,
                        area=ImagemapArea(x=x, y=y, width=width, height=height), )
                    action_content.append(action_single)
                elif action_type == "check_bind_url":
                    account_bing = check_account_bind(im_id)
                    if account_bing == 1:
                        url_key = action["url_key"]
                        url = check_url(url_key, im_id)
                        link_uri = action["link_uri"] + url
                        x = action["area"]["x"]
                        y = action["area"]["y"]
                        width = action["area"]["width"]
                        height = action["area"]["height"]
                        action_single = URIImagemapAction(
                            link_uri=link_uri,
                            area=ImagemapArea(x=x, y=y, width=width, height=height), )
                        action_content.append(action_single)

                    else:
                        text = "尚未開啟帳務服務"
                        x = action["area"]["x"]
                        y = action["area"]["y"]
                        width = action["area"]["width"]
                        height = action["area"]["height"]
                        action_single = MessageImagemapAction(
                            text=text,
                            area=ImagemapArea(x=x, y=y, width=width, height=height), )
                        action_content.append(action_single)

                elif action_type == "url":
                    link_uri = action["link_uri"]
                    x = action["area"]["x"]
                    y = action["area"]["y"]
                    width = action["area"]["width"]
                    height = action["area"]["height"]
                    action_single = URIImagemapAction(
                        link_uri=link_uri,
                        area=ImagemapArea(x=x, y=y, width=width, height=height), )
                    action_content.append(action_single)

                elif action_type == "message":
                    text = action["text"]
                    x = action["area"]["x"]
                    y = action["area"]["y"]
                    width = action["area"]["width"]
                    height = action["area"]["height"]
                    action_single = MessageImagemapAction(
                        text=text,
                        area=ImagemapArea(x=x, y=y, width=width, height=height), )

                    action_content.append(action_single)
                elif action_type == "button":
                    x = action["area"]["x"]
                    y = action["area"]["y"]
                    width = action["area"]["width"]
                    height = action["area"]["height"]
                    main_title = action["text"]

                    action_single = CarouselColumn(
                            text=main_title,
                            thumbnail_image_url=img_url,
                            actions=button_data
                        )


            return action_content

        def check_template_type(button_content, im_id):
            button_type = button_content["Type"]
            logger.info(button_type)
            template_message = ""

            if button_type == "ButtonsTemplate":
                actions = check_action(button_content["Content"]["actions"], im_id)
                text = button_content["Content"]["text"]
                template = ButtonsTemplate(
                    text=text,
                    actions=actions)
                template_message = TemplateSendMessage(
                    alt_text='綁定帳號起在手機上使用', template=template)

            if button_type == "ImagemapSendMessage":
                actions = check_imagemap_action(button_content["Content"]["actions"], im_id)
                title = button_content["Content"]["title"]
                image_url = button_content["Content"]["base_url"]
                image_height = button_content["Content"]["height"]
                image_width = button_content["Content"]["width"]

                template_message = ImagemapSendMessage(
                    base_url=image_url,
                    alt_text=title,
                    base_size=BaseSize(height=image_height, width=image_width),
                    actions=actions
                )
            if button_type == "textMessage":
                text = button_content["text"]
                template_message = TextSendMessage(text=text)

            return template_message

        def send_line_test_message(reply_token, im_id, key_content):
            template = check_template_type(key_content, im_id)
            self.line_bot_api.reply_message(reply_token, template)

        def action_word_message(reply_token, im_id, action_content):
            template = check_template_type(action_content, im_id)
            self.line_bot_api.reply_message(reply_token, template)

    def line_check_elements_type(self, elements_data_detail, check_user):
        carousel_template_all = []
        carousel_template = []
        for data in elements_data_detail:
            if "TEXT" == data["TYPE"]:
                if "MSG" in data:
                    main_title = data["MSG"]
                else:
                    main_title = ""
                json_data = TextSendMessage(text=main_title)

            elif "MEDIA" == data["TYPE"]:

                if not "" == data["TITLE"]:
                    main_title = data["TITLE"]
                else:
                    main_title = None

                if not "" == data["IMG-URL"]:
                    img_url = data["IMG-URL"]
                else:
                    img_url = None

                '''if not "" == data["SUBTITLE"]:
                    main_subtitle = data["SUBTITLE"]
                else:
                    main_subtitle = None'''
                button_data = None
                if not [] == data["BUTTONS"]:
                    buttons = data["BUTTONS"]
                    button_data = self.count_button_data(buttons, check_user)

                if not [] == data["ACTIONS"]:
                    buttons = data["ACTIONS"]
                    button_data = self.count_button_data(buttons, check_user)

                if button_data is not None:
                    button_count = len(button_data)
                    if len(button_data) > 3:
                        while button_count > 0:
                            del_number = button_count % 3
                            if del_number == 0:
                                del_number = 3
                            if button_count - del_number != 0:
                                carousel_template_all.insert(0,
                                                             CarouselColumn(
                                                                 text="你可能也想知道",
                                                                 thumbnail_image_url=img_url,
                                                                 actions=button_data[
                                                                         button_count - del_number:button_count]
                                                             ))
                            else:
                                carousel_template_all.insert(0,
                                                             CarouselColumn(
                                                                 text=main_title,
                                                                 thumbnail_image_url=img_url,
                                                                 actions=button_data[0:del_number]
                                                             )
                                                             )
                            button_count = button_count - del_number

                if None is not button_data:
                    if len(elements_data_detail) == 1 and len(button_data) <= 3:
                        if None is img_url:
                            button_template = ButtonsTemplate(
                                text=main_title,
                                actions=button_data
                            )
                            json_data = TemplateSendMessage(
                                alt_text="請在您的手機上觀看相關訊息",
                                template=button_template
                            )
                        else:
                            button_template = ButtonsTemplate(
                                text=main_title,
                                actions=button_data,
                                thumbnail_image_url=img_url
                            )
                            json_data = TemplateSendMessage(
                                alt_text="請在您的手機上觀看相關訊息",
                                template=button_template
                            )

                    elif len(elements_data_detail) > 1 and len(button_data) <= 3:
                        carousel_template = CarouselColumn(
                            text=main_title,
                            thumbnail_image_url=img_url,
                            actions=button_data
                        )
                        logger.info(carousel_template)
                        carousel_template_all.append(carousel_template)

        if len(carousel_template_all) > 1:
            logger.info(carousel_template_all)
            carousel = CarouselTemplate(columns=carousel_template_all)
            json_data = TemplateSendMessage(alt_text='請在您的手機上觀看相關訊息', template=carousel)
        return json_data

    def count_button_data(self, buttons, check_user):
        if len(buttons) > 0:
            button_data = []
            for button in buttons:
                if len(button_data) < 15:
                    button_text = button["TEXT"]
                    if False is check_user:
                        button_text = self.group_keyword + button_text
                    label_text = self.check_text(button["TEXT"])
                    if "" == button["URL"]:
                        button_data.append(MessageTemplateAction(
                            label=label_text,
                            text=button_text
                        ))
                    else:
                        button_data.append(URITemplateAction(
                            label=label_text,
                            uri=button["URL"]
                        ))
                else:
                    continue
        else:
            button_data = None
        if None is not button_data:
            if len(button_data) % 3 != 0 and len(button_data) > 3:
                button_data_length = len(button_data)
                del_number = button_data_length % 3
                button_data = button_data[0:button_data_length - del_number]

        return button_data

    def check_text(self, text):
        if len(text) > 20:
            new_text = text[0:18]
        else:
            new_text = text
        return new_text

    def log(message):  # simple wrapper for logging to stdout on heroku
        sys.stdout.flush()

    def run(self):
        self.application.run(host='0.0.0.0',port=self.port, )

    # def conn_close(self):
    #     self.conn.close()
    #     self.conn = None

    def connect_db(self):
        host = self.db_connect_host
        user = self.db_connect_name
        password = self.db_connect_password
        db = self.db_connect_db
        connection = pymysql.connect(host=host,
                                     user=user,
                                     password=password,
                                     db=db,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor,
                                     autocommit=True)

        return connection

    def search_room_id(self, im_id):
        chat_room_id = ''
        global global_locker
        global_locker.acquire()
        for i in range(0,3):
            try:
                if self.conn is None:
                    self.conn = self.connect_db()
                if self.conn:
                    c = self.conn.cursor()
                    c.execute("SELECT `ChatRoomID`,`LastAccessTime` FROM `Member_lineuser` WHERE `SourceID`=%s ", (im_id,))
                    raw_chat_room_id = c.fetchone()
                    now = datetime.datetime.now()
                    if raw_chat_room_id is None:
                        source = self.source
                        profile = self.line_bot_api.get_profile(im_id)
                        name = profile.display_name
                        avatar_url = profile.picture_url
                        chat_room_id = uuid.uuid4().hex
                        c.execute(
                            "INSERT INTO `Member_lineuser` ( `SourceID` , `CreateTime`, `LastAccessTime`, `NickName`, `IconURL`, `GetInfoTime`"
                            ", `ExtraInfo`, `ChatRoomID`, `Enabled`, `Source_id`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (im_id, now, now, name, avatar_url, now, "something have to store", chat_room_id, 1, source))
                        self.conn.commit()

                    else:
                        last_access_time = raw_chat_room_id["LastAccessTime"]
                        chat_room_id = raw_chat_room_id["ChatRoomID"]
                        if now > last_access_time + datetime.timedelta(days=1):
                            profile = self.line_bot_api.get_profile(im_id)
                            avatar_url = profile.picture_url
                            c.execute("UPDATE Member_lineuser SET IconURL=%s ,LastAccessTime=%s WHERE ChatRoomID=%s",( avatar_url, now, chat_room_id))
                            self.conn.commit()

            except BaseException as e:
                # self.conn_close()
                logger.exception('update_ga_group exception' + str(e))
            finally:
                if len(chat_room_id) > 0:
                    break
        global_locker.release()

        return chat_room_id

    def write_db(self, room_id, im_id, content, meg_type, meg_status):
        now = datetime.datetime.now()
        msg_error_count = 0
        text_content = content
        try:
            if self.conn is None:
                self.conn = self.connect_db()
            if self.conn:
                c = self.conn.cursor()
                if len(text_content) >= 500:
                    logger.exception('reply_content > 500:' + text_content)
                    text_content = '{"ELEMENTS":[[{"TYPE":"MEDIA","IMG-URL":"","IMG-LINK":"","TITLE":"TEMPLATE過長"}]]}'
                c.execute(
                    "INSERT INTO `Room_room` (`ChatRoomID`,`SenderID`,`Message`,`MessageType`,`MessageStutus`,`MsgErrorCount`,`CreateTime`,`UpdateTime`,`Sender`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (room_id, im_id, text_content, meg_type, meg_status, msg_error_count, now, now, 'Line'))
                self.conn.commit()
        except BaseException as e:
            # self.conn_close()
            logger.exception('update_ga_group exception' + str(e))

    def write_user_history(self, action_type, action_content, im_id):
        now = datetime.datetime.now()
        try:
            if self.conn is None:
                self.conn = self.connect_db()
            if self.conn:
                c = self.conn.cursor()
                c.execute("SELECT `id` FROM `Member_lineuser` WHERE `SourceID`=%s ", (im_id,))
                raw_chat_room_id = c.fetchone()
                if raw_chat_room_id is not None:
                    line_user_id = raw_chat_room_id["id"]
                    c.execute("INSERT INTO `member_userhistory` (`ActionType`,`ActionContent`,`Time`,`Source_id`,`SourceID_id`) VALUES (%s,%s,%s,%s,%s)",(action_type, action_content, now, self.source, line_user_id))
                    self.conn.commit()
        except BaseException as e:
            # self.conn_close()
            logger.exception('Update_user_history exception' + str(e))

    # def update_alive_status(self, system_key):
    #     global global_locker
    #     global_locker.acquire()
    #     try:
    #
    #         if self.conn is None:
    #             self.conn = self.connect_db()
    #         if self.conn:
    #             c = self.conn.cursor()
    #             now = datetime.datetime.now()
    #
    #             c.execute("UPDATE othermanagement_system_alive SET LastAliveTime=%s WHERE SystemKey=%s",(now, system_key))
    #             self.conn.commit()
    #     except BaseException as e:
    #         # self.conn_close()
    #         logger.exception('sqlite_question_count_update exception' + str(e))
    #     finally:
    #         global_locker.release()

    # def thread_alive(self, gw_name):
    #     try:
    #         while (True):
    #             self.update_alive_status(gw_name)
    #             time.sleep(30)
    #     except:
    #         logger.exception(traceback.format_exc())


def thread_function(gw):
    gw.run()


if __name__ == "__main__":
    logger.info("Start Line_GW")
    thread_list = []
    # for i in range(10):
    #     gw_port = 9000 + i
    #     gw = LineGW(port=gw_port)
    #     gw_name = "LG" + str(i+1)
    #     thread_list.append(threading.Thread(target=thread_function, args=(gw,)))

    gw = LineGW(port=9999)
    gw.run()
    # for t in thread_list:
    #     t.start()
    # for t in thread_list:
    #     t.join()
