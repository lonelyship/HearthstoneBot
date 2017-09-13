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

from getXVideo import getXvideos

from random import randint

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
mRaceDict={"德魯伊":"Druid","德":"Druid",
           "薩滿":"Shaman","薩":"Shaman",
           "術士":"Warlock","術":"Warlock",
           "盜賊":"Rogue","盜":"Rogue",
           "聖騎士":"Paladin","聖":"Paladin","聖騎":"Paladin",
           "牧師":"Priest","牧":"Priest",
           "中立":"Neutral",
           "戰士":"Warrior","戰":"Warrior",
           "獵人":"Hunter","獵":"Hunter",
           "法師":"Mage","法":"Mage",}
mRace = ""
mRaceName = ""


mCostDict={
           "一費":1,"1費":1,
           "二費":2,"2費":2,
           "三費":3,"3費":3,
           "四費":4,"4費":4,
           "五費":5,"5費":5,
           "六費":6,"6費":6,
           "七費":7,"7費":7,
           "八費":8,"8費":8,
           "九費":9,"9費":9,
           "十費":10,"10費":10,
           "十ㄧ費":11,"11費":11,
           "十二費":12,"12費":12,
           "二十費":20,"20費":20,
           "三十費":30,"30費":30,
           }
mCost = ""
mCostName = ""

mXData=[]
mXIndex = 0
mXGroup = 0

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

            global mAllIndex
            global mAllGroup
            global mAllData
            global mRaceDict
            global mRace
            global mRaceName
            global mCostDict
            global mCost
            global mCostName

            global mXData
            global mXIndex
            global mXGroup

            if text.startswith("!"):
                text = text.replace("!", "")
                if text == 'X' or text == 'x' or text =='下一頁' or text =='上一頁' or text =='隨機' or text =='第一頁':
                    if text == '上一頁':
                        if mXIndex - 8>=0:
                            mXIndex = mXIndex-8
                    if text == '隨機':
                        mXIndex = randint(0, len(mXData)-4)
                    if text == '第一頁':
                            mXIndex = 0
                    if len(mXData) == 0:
                        mXData = getXvideos(5)
                    searchX(event)

            if text.startswith("@"):
                text= text.replace("@","")
            elif text.startswith("＠"):
                text= text.replace("＠","")
            else:
                return


            if text == '重置':
                reset(event)

            if text == '職業篩選':
                getAllRace(event)

            if text == '費用篩選':
                getAllCost(event)

            if text in  mRaceDict:
                mRace=mRaceDict[text]
                mRaceName = text
                resetFilter(event)

            if text in  mCostDict:
                mCost=mCostDict[text]
                mCostName = text
                resetFilter(event)

            if text == '查詢' or text == '下一頁':
                if text == '查詢':
                    initial()
                search(event)


            fuzzySearch(event,text)


        def searchX(event):
            global mXData
            global mXIndex
            global mXGroup

            ObjArray = []
            count = 0
            if len(mXData) > 0:
                bIsFirst = True
                for i in range(mXIndex, len(mXData) - 1):
                    item = mXData[i]
                    tempIndex = i
                    if 'img' in item and 'link' in item and 'title' in item:
                        if tempIndex % 4 == 0 and bIsFirst == False:
                            buttons_template_message_more = TemplateSendMessage(
                                alt_text='點擊下方功能看更多',
                                template=ButtonsTemplate(
                                    text='換頁',
                                    actions=[
                                        MessageTemplateAction(
                                            label='上一頁 ',
                                            text='!上一頁'
                                        ),
                                        MessageTemplateAction(
                                            label='下一頁 ',
                                            text='!下一頁'
                                        ),
                                        MessageTemplateAction(
                                            label='隨機 ',
                                            text='!隨機'
                                        ),
                                        MessageTemplateAction(
                                            label='第一頁 ',
                                            text='!第一頁'
                                        ),
                                    ]
                                )
                            )
                            ObjArray.append(buttons_template_message_more)


                            mXIndex = tempIndex
                            break;
                        bIsFirst = False

                        actions = []
                        actions.append(URITemplateAction(
                            label='preview',
                            uri=mXData[tempIndex]['img'],
                        ))
                        actions.append(URITemplateAction(
                                    label='play',
                                    uri=mXData[tempIndex]['link'],
                                ))

                        buttons_template_message = TemplateSendMessage(
                                thumbnail_image_url=mXData[tempIndex]['img'].replace("http", "https"),
                                alt_text='!!',
                                template=ButtonsTemplate(
                                    text=mXData[tempIndex]['title'],
                                    actions=actions
                                )
                            )

                        ObjArray.append(buttons_template_message)
                    else:
                        continue;

                if len(ObjArray) == 0:
                    text = TextSendMessage(text="查無資料")
                    self.line_bot_api.reply_message(event.reply_token, text)

                self.line_bot_api.reply_message(event.reply_token, ObjArray)
                return

        def initial():
            global mAllIndex
            global mAllGroup
            mAllIndex = 0
            mAllGroup = 0

        def getAllRace(event):
            ObjArray = []
            actions1 = []
            actions1.append(MessageTemplateAction(
                label="法師",
                text='@法師',
            ))
            actions1.append(MessageTemplateAction(
                label="德魯伊",
                text='@德魯伊',
            ))
            actions1.append(MessageTemplateAction(
                label="盜賊",
                text='@盜賊',
            ))
            actions1.append(MessageTemplateAction(
                label="術士",
                text='@術士',
            ))
            buttons_template_message_1 = TemplateSendMessage(
                alt_text='點擊下方職業查詢',
                template=ButtonsTemplate(
                    text='點擊下方職業查詢',
                    actions=actions1
                )
            )

            actions2 = []
            actions2.append(MessageTemplateAction(
                label="聖騎士",
                text='@聖騎士',
            ))
            actions2.append(MessageTemplateAction(
                label="獵人",
                text='@獵人',
            ))
            actions2.append(MessageTemplateAction(
                label="牧師",
                text='@牧師',
            ))
            actions2.append(MessageTemplateAction(
                label="戰士",
                text='@戰士',
            ))
            buttons_template_message_2 = TemplateSendMessage(
                alt_text='點擊下方職業查詢',
                template=ButtonsTemplate(
                    text='點擊下方職業查詢',
                    actions=actions2
                )
            )

            actions3 = []
            actions3.append(MessageTemplateAction(
                label="薩滿",
                text='@薩滿',
            ))
            actions3.append(MessageTemplateAction(
                label="中立",
                text='@中立',
            ))

            buttons_template_message_3 = TemplateSendMessage(
                alt_text='點擊下方職業查詢',
                template=ButtonsTemplate(
                    text='點擊下方職業查詢',
                    actions=actions3
                )
            )

            ObjArray.append(buttons_template_message_1)
            ObjArray.append(buttons_template_message_2)
            ObjArray.append(buttons_template_message_3)
            self.line_bot_api.reply_message(event.reply_token, ObjArray)
            initial()
            return

        def getAllCost(event):
            ObjArray = []
            actions1 = []
            actions1.append(MessageTemplateAction(
                label="1費",
                text='@1費',
            ))
            actions1.append(MessageTemplateAction(
                label="2費",
                text='@2費',
            ))
            actions1.append(MessageTemplateAction(
                label="3費",
                text='@3費',
            ))
            actions1.append(MessageTemplateAction(
                label="4費",
                text='@4費',
            ))
            buttons_template_message_1 = TemplateSendMessage(
                alt_text='點擊下方費用查詢',
                template=ButtonsTemplate(
                    text='點擊下方費用查詢',
                    actions=actions1
                )
            )

            actions2 = []
            actions2.append(MessageTemplateAction(
                label="5費",
                text='@5費',
            ))
            actions2.append(MessageTemplateAction(
                label="6費",
                text='@6費',
            ))
            actions2.append(MessageTemplateAction(
                label="7費",
                text='@7費',
            ))
            actions2.append(MessageTemplateAction(
                label="8費",
                text='@8費',
            ))
            buttons_template_message_2 = TemplateSendMessage(
                alt_text='點擊下方費用查詢',
                template=ButtonsTemplate(
                    text='點擊下方費用查詢',
                    actions=actions2
                )
            )

            actions3 = []
            actions3.append(MessageTemplateAction(
                label="9費",
                text='@9費',
            ))
            actions3.append(MessageTemplateAction(
                label="10費",
                text='@10費',
            ))
            actions3.append(MessageTemplateAction(
                label="11費",
                text='@11費',
            ))
            actions3.append(MessageTemplateAction(
                label="12費",
                text='@12費',
            ))

            buttons_template_message_3 = TemplateSendMessage(
                alt_text='點擊下方費用查詢',
                template=ButtonsTemplate(
                    text='點擊下方費用查詢',
                    actions=actions3
                )
            )

            ObjArray.append(buttons_template_message_1)
            ObjArray.append(buttons_template_message_2)
            ObjArray.append(buttons_template_message_3)
            self.line_bot_api.reply_message(event.reply_token, ObjArray)
            initial()
            return

        def resetFilter(event):
            ObjArray = []
            global mRaceName
            global mCostName
            raceName = "所有"
            costName = "所有"

            if mRaceName!="":
                raceName = mRaceName

            if mCostName!="":
                costName = mCostName

            textObj = TextSendMessage(text="更新篩選條件:"+"["+"職業:"+raceName+"  "+"費用:"+costName+"]")
            ObjArray.append(textObj)
            actions = []
            actions.append(MessageTemplateAction(
                label="查詢",
                text='@查詢',
            ))
            buttons_template_message = TemplateSendMessage(
                alt_text='點擊下方功能查詢',
                template=ButtonsTemplate(
                    text='點擊下方功能查詢',
                    actions=actions
                )
            )

            ObjArray.append(buttons_template_message)
            self.line_bot_api.reply_message(event.reply_token, ObjArray)
            initial()
            return


        def reset(event):
             global mAllIndex
             global mAllGroup
             global mAllData
             global mRace
             global mRaceName
             global mCost
             global mCostName
             mAllIndex = 0
             mAllGroup = 0

             mRace = ""
             mRaceName = ""
             mCost =""
             mCostName = ""
             text = TextSendMessage(text="條件已重置")
             self.line_bot_api.reply_message(event.reply_token, text)
             return

        def search(event):
            global mAllIndex
            global mAllGroup
            global mAllData
            global mRace
            global mCost
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
                                alt_text='點擊下方功能看更多',
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

                        if mRace != "" and 'playerClass' in item and item["playerClass"] != mRace:
                            continue
                        if mCost !="" and  'cost' in item and item["cost"] != mCost:
                            continue

                        name = item['name']
                        nameArray.append(name)
                        count = count + 1;
                        if count != 0 and count % 4 == 0:
                            mAllGroup = mAllGroup + 1
                            actions = []
                            index = 0
                            for nameItem in nameArray:
                                index = index + 1
                                actions.append(MessageTemplateAction(
                                    label=str((mAllGroup-1)*4+index)+"."+nameItem,
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
                                alt_text='點擊下方卡牌查詢',
                                template=ButtonsTemplate(
                                    text="點擊下方卡牌查詢",
                                    actions=actions
                                )
                            )
                            # self.line_bot_api.reply_message(event.reply_token, buttons_template_message)
                            # return
                            ObjArray.append(buttons_template_message)
                            nameArray = []

                    else:
                        continue;

            if len(ObjArray) == 0:
                text = TextSendMessage(text="查無資料")
                self.line_bot_api.reply_message(event.reply_token, text)
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
                                        alt_text='你可能還會想知道',
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

                return



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
