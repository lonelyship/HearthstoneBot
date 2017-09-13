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

mAllData = []
mAllIndex = 0
mAllGroup = 0
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

            if text == '重置':
                reset(event)

            elif text == '查詢' or text == '下一頁':
                search(event)
            else:
                fuzzySearch(event,text)


        def reset(event):
             global mAllIndex
             global mAllGroup
             global mAllData
             mAllIndex = 0
             mAllGroup = 0
             mAllData = []
             text = TextSendMessage(text="條件已重置")
             self.line_bot_api.reply_message(event.reply_token, text)
             return

        def search(event):
            global mAllIndex
            global mAllGroup
            global mAllData
            if len(mAllData) == 0:
                url = 'https://omgvamp-hearthstone-v1.p.mashape.com/cards/';
                headers = {'X-Mashape-Key': 'zJ6HmBMQfamshXuEdrPbQ9QmIMtrp1yaw7hjsnLY3DeERkqtQI'}
                params = dict(
                    locale='zhTW',
                )

                resp = requests.get(url=url, params=params, headers=headers)
                data = json.loads(resp.text)

                for key, value in data.items():
                    # print("Key:", key)
                    for item in data[key]:
                        mAllData.append(item)

            # print(allData)

            nameArray = []
            actions = []
            ObjArray = []
            count = 0

            if len(mAllData) > 0:
                for i in range(mAllIndex, len(mAllData) - 1):
                    item = mAllData[i]
                    tempIndex = i
                    if 'img' in item and 'text' in item and 'name' in item:
                        if count % 16 == 0 and count != 0:
                            buttons_template_message_more = TemplateSendMessage(
                                alt_text='Buttons template',
                                template=ButtonsTemplate(
                                    text='看更多',
                                    actions=[

                                        MessageTemplateAction(
                                            label='下一頁',
                                            text='@下一頁'
                                        )
                                    ]
                                )
                            )
                            ObjArray.append(buttons_template_message_more)
                            mAllIndex = tempIndex
                            break;
                        name = item['name']
                        nameArray.append(name)
                        count = count + 1;
                        if count != 0 and count % 4 == 0:
                            mAllGroup = mAllGroup + 1
                            actions = []
                            for nameItem in nameArray:
                                actions.append(MessageTemplateAction(
                                    label=nameItem,
                                    text='@' + nameItem,
                                ))

                            # buttons_template_message = TemplateSendMessage(
                            #     alt_text='Buttons template',
                            #     template=ButtonsTemplate(
                            #         thumbnail_image_url='https://example.com/image.jpg',
                            #         title='Menu',
                            #         text='Please select',
                            #         actions=[
                            #             PostbackTemplateAction(
                            #                 label='postback',
                            #                 text='postback text',
                            #                 data='action=buy&itemid=1'
                            #             ),
                            #             MessageTemplateAction(
                            #                 label='message',
                            #                 text='message text'
                            #             ),
                            #             URITemplateAction(
                            #                 label='uri',
                            #                 uri='http://example.com/'
                            #             )
                            #         ]
                            #     )
                            # )
                            buttons_template_message = TemplateSendMessage(
                                alt_text='Buttons template',
                                template=ButtonsTemplate(
                                    text='第' + str(mAllGroup) + '組',
                                    actions=actions
                                )
                            )
                            # self.line_bot_api.reply_message(event.reply_token, buttons_template_message)
                            # return
                            ObjArray.append(buttons_template_message)
                            nameArray = []

                    else:
                        continue;

            self.line_bot_api.reply_message(event.reply_token, ObjArray)
            return
        def fuzzySearch(event,text):
            url = 'https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/' + text;
            headers = {'X-Mashape-Key': 'zJ6HmBMQfamshXuEdrPbQ9QmIMtrp1yaw7hjsnLY3DeERkqtQI'}
            params = dict(
                locale='zhTW',
            )

            resp = requests.get(url=url, params=params, headers=headers)
            data = json.loads(resp.text)

            count = 0;
            ObjArray = []
            nameArray = []
            actions = []
            if len(data) > 0:
                for item in data:
                    if 'img' in item and 'text' in item and 'name' in item:
                        if len(ObjArray) >= 5:
                            break;
                        count = count + 1
                        if count == 1:
                            imgurl = item['img'].replace("http", "https")
                            # print("!!!!!", imgurl)

                            import re
                            cleanr = re.compile('<.*?>')
                            cleantext = re.sub(cleanr, '', item['text'])
                            cleantext = cleantext.replace('\\n', '\n')

                            textObj = TextSendMessage(text=item['name'] + "\n" + cleantext)
                            imgObj = ImageSendMessage(
                                original_content_url=imgurl,
                                preview_image_url=imgurl
                            )

                            ObjArray.append(textObj)
                            ObjArray.append(imgObj)

                        else:
                            name = item['name']
                            nameArray.append(name)
                            if count != 1 and count % 4 == 1:
                                actions = []
                                for nameItem in nameArray:
                                    actions.append(MessageTemplateAction(
                                        label=nameItem,
                                        text='@' + nameItem,
                                    ))
                                    buttons_template_message = TemplateSendMessage(
                                        alt_text='Buttons template',
                                        template=ButtonsTemplate(
                                            text='你可能還會想知道',
                                            actions=actions
                                        )
                                    )
                                ObjArray.append(buttons_template_message)
                                nameArray = []
                                # break;

                    else:
                        continue;

                if count == 0:
                    text = TextSendMessage(text="查無資料")
                    self.line_bot_api.reply_message(event.reply_token, text)
                else:
                    self.line_bot_api.reply_message(event.reply_token, ObjArray)



        @handler.add(MessageEvent, message=StickerMessage)
        def handle_sticker_message(event):
            logger.info("Line get sticker :%s Line_id = %s", event.message.sticker_id, event.source.user_id)

            self.line_bot_api.reply_message(
                event.reply_token,
                StickerSendMessage(
                    package_id=event.message.package_id,
                    sticker_id=event.message.sticker_id)
            )


    def log(message):  # simple wrapper for logging to stdout on heroku
        sys.stdout.flush()

    def run(self):
        self.application.run(host='0.0.0.0',port=self.port, )

    # def conn_close(self):
    #     self.conn.close()
    #     self.conn = None

    # def connect_db(self):
    #     host = self.db_connect_host
    #     user = self.db_connect_name
    #     password = self.db_connect_password
    #     db = self.db_connect_db
    #     connection = pymysql.connect(host=host,
    #                                  user=user,
    #                                  password=password,
    #                                  db=db,
    #                                  charset='utf8mb4',
    #                                  cursorclass=pymysql.cursors.DictCursor,
    #                                  autocommit=True)
    #
    #     return connection
    #
    # def write_db(self, room_id, im_id, content, meg_type, meg_status):
    #     now = datetime.datetime.now()
    #     msg_error_count = 0
    #     text_content = content
    #     try:
    #         if self.conn is None:
    #             self.conn = self.connect_db()
    #         if self.conn:
    #             c = self.conn.cursor()
    #             if len(text_content) >= 500:
    #                 logger.exception('reply_content > 500:' + text_content)
    #                 text_content = '{"ELEMENTS":[[{"TYPE":"MEDIA","IMG-URL":"","IMG-LINK":"","TITLE":"TEMPLATE過長"}]]}'
    #             c.execute(
    #                 "INSERT INTO `Room_room` (`ChatRoomID`,`SenderID`,`Message`,`MessageType`,`MessageStutus`,`MsgErrorCount`,`CreateTime`,`UpdateTime`,`Sender`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
    #                 (room_id, im_id, text_content, meg_type, meg_status, msg_error_count, now, now, 'Line'))
    #             self.conn.commit()
    #     except BaseException as e:
    #         # self.conn_close()
    #         logger.exception('update_ga_group exception' + str(e))

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
