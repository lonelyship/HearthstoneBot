import requests
import json
import pytz
import datetime
from datetime import timedelta

# 目前想的操作流程
# 1.查詢列出所有高鐵站 => queryAllStation
# 2.選擇[起始車站]
# 3.選擇[終點車站]
# 4.選擇[日期]
# 5-1.查詢票價&各車次時刻表 => queryDailyTimetable_OD([起始車站ID][終點車站ID][日期%Y-%m-%d])
# 5-1-2.查詢剩餘座位狀態 => queryAvailableSeatStatusList([起始車站ID], [車次ID])
# 　
class THSRApi:
    THSR_Station_Url = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/Station?$format=JSON"
    THSR_ODFare_Url = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/ODFare/%s/to/%s?$format=JSON"
    THSR_DailyTimetable_OD_Url = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/OD/%s/to/%s/%s?$format=JSON"
    THSR_AvailableSeatStatus_List_Url = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/AvailableSeatStatusList/%s?$format=JSON"
    THSR_News_Url = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/News?$top=5&$format=JSON"
    # THSR_DailyTimetable = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/Station/%s/%s?$format=JSON"

    station_map = {}#暫存所有車站

    # 查詢所有高鐵站的車站ID
    def queryAllStation(self):
        # print(self.THSR_Station_Url)
        response = requests.get(self.THSR_Station_Url)
        jsonarray = json.loads(response.text)
        result = []
        for jsonobj in jsonarray:
            station_name = jsonobj['StationName']['Zh_tw']
            station_id = jsonobj['StationID']
            item = {}
            item['station_name'] = station_name
            item['station_id'] = station_id
            result.append(item)

        result = sorted(result, key=lambda k: k['station_id'], reverse=False) #依車站ID排序

        self.station_map = self.parseStationJsonToMap(result)

        # print(result)
        return result

    # 查詢指定[起始車站ID][終點車站ID][日期]的站別時刻表資料及票價資料
    def queryDailyTimetable_OD(self, StartStationId, DestinationStationId, TrainDate):

        start_station_id = StartStationId
        destination_station_id = DestinationStationId

        # 名稱轉換ID
        if start_station_id.isdigit() == False:
            start_station_id = self.findStationIdFromStationName(StartStationId)
        if destination_station_id.isdigit() == False:
            destination_station_id = self.findStationIdFromStationName(DestinationStationId)
        if start_station_id != None and destination_station_id != None:
            request_url = self.THSR_DailyTimetable_OD_Url % (start_station_id, destination_station_id, TrainDate)
        else:
            # print('找不到ID')
            return None

        fare = self.queryODFare(start_station_id, destination_station_id);#先查票價資料
        # print(request_url)
        response = requests.get(request_url)

        jsonarray = json.loads(response.text)

        result = {}
        results = []

        for jsonObj in jsonarray:
            taindate = jsonObj['OriginStopTime']['ArrivalTime']
            if self.compareTime(taindate, '%H:%M'):
                # 篩選掉出發時間小於現在時間的資料
                title = jsonObj['OriginStopTime']['StationName']['Zh_tw'] + '->' + jsonObj['DestinationStopTime']['StationName']['Zh_tw']
                train_id = jsonObj['DailyTrainInfo']['TrainNo']
                departure_time = jsonObj['OriginStopTime']['ArrivalTime']
                arrival_time = jsonObj['DestinationStopTime']['ArrivalTime']
                item = {}
                item['title'] = title #標題
                item['train_id'] = train_id #車次ID
                item['departure_time'] = departure_time #出發時間
                item['arrival_time'] = arrival_time #抵達時間
                results.append(item)

        results = sorted(results, key=lambda k: k['departure_time'], reverse=False)  # 依出發時間排序

        if results.__len__() > 0:
            result['fare'] = fare
            result['trains_data'] = results

        print(result)
        return result

    #查詢[起始站ID]和[終點站ID]的票價
    def queryODFare(self, OriginStationID, DestinationStationID):
        requestUrl = self.THSR_ODFare_Url %(OriginStationID,DestinationStationID)
        # print(requestUrl)
        r = requests.get(requestUrl)
        jsonarray = json.loads(r.text)
        result = []
        for jsonObj in jsonarray:
            jsonArrayFares = jsonObj['Fares'];
            for fare in jsonArrayFares:
                ticket_name = fare['TicketType']
                price = fare['Price']
                item = {}
                item['ticket_name'] = ticket_name
                item['price'] = price
                result.append(item)

        result = sorted(result, key=lambda k: k['price'], reverse=False)  #依價格排序
        # print(result)
        return result

    # 查詢指定車站，指定車次的剩餘座位
    def queryAvailableSeatStatusList(self, StationId, TrainId):
        requestUrl = self.THSR_AvailableSeatStatus_List_Url % StationId
        print(requestUrl)
        response = requests.get(requestUrl)
        jsonarray = json.loads(response.text)[0]['AvailableSeats']
        result = []
        for jsonobj in jsonarray:
            if jsonobj['TrainNo'] == TrainId:
                print(jsonobj['TrainNo'])
                start_station = jsonobj['StationName']['Zh_tw']
                for station in jsonobj['StopStations']:
                    title = start_station + '->' + station['StationName']['Zh_tw']
                    standard_seat_status = station['StandardSeatStatus']
                    business_seat_status = station['BusinessSeatStatus']
                    print('標題:' + title)
                    print('標準席:' + standard_seat_status)
                    print('商務席:' + business_seat_status)
                    item = {}
                    item['title'] = title #台北->台中
                    item['standard_seat'] = self.getSeatAvailableString(standard_seat_status)
                    item['business_seat'] = self.getSeatAvailableString(business_seat_status)
                    result.append(item)
        #
        # print(result)
        # print(result.__len__())
        return result

    def queryNews(self):
        print(self.THSR_News_Url)
        response = requests.get(self.THSR_News_Url)
        print(response.text)

    #查詢回傳最近三天的日期
    # result[0]今天
    # result[1]明天
    # result[2]後天
    def qeuryLastestDate(self):

        result = []

        # 取得台灣時區的時間 方法一
        dtToday = datetime.datetime.now(pytz.timezone('Asia/Taipei'))
        # print(dtToday.strftime('%Y-%m-%d %H:%M'))
        # jsonToday = {};
        # jsonToday['datetime'] = dtToday.strftime('%Y-%m-%d')
        result.append(dtToday.strftime('%Y-%m-%d'))

        dtTomorrow = dtToday + timedelta(days = 1)
        # print(dtTomorrow.strftime('%Y-%m-%d %H:%M'))
        # jsonTomorrow = {};
        # jsonTomorrow['datetime'] = dtTomorrow.strftime('%Y-%m-%d')
        result.append(dtTomorrow.strftime('%Y-%m-%d'))

        dtPostnatal = dtToday + timedelta(days = 2)
        # print(dtPostnatal.strftime('%Y-%m-%d %H:%M'))
        # jsonPostnatal = {};
        # jsonPostnatal['datetime'] = dtPostnatal.strftime('%Y-%m-%d')
        result.append(dtPostnatal.strftime('%Y-%m-%d'))

        # for day in result:
        #     print(day['datetime'])

        # print(result)

        return result

        # 取得台灣時區的時間 方法二
        # dt = datetime.utcnow()
        # print(dt)
        # dt = dt.replace(tzinfo=timezone.utc)
        # print(dt)
        # tzutc_8 = timezone(timedelta(hours=8))
        # local_dt = dt.astimezone(tzutc_8)
        # print(local_dt)
        # print(local_dt.strftime('%Y-%m-%d'))

    # 比對時間
    # 回傳 true : 傳入時間 > 目前時間
    #     false : 傳入時間 < 目前時間
    def compareTime(self, time, timeformat):
        compareTime = datetime.datetime.strptime(time, timeformat)
        now = datetime.datetime.now(pytz.timezone('Asia/Taipei'))
        # print('compareTime:' + compareTime.strftime('%H:%M'))
        # print('now:' + now.strftime('%H:%M'))
        result = compareTime.time() > now.time()
        # print(result)
        return result

    def getSeatAvailableString(self, AvailableStatus):
        # ['Available: 尚有座位' or 'Limited: 座位有限' or 'Full: 已無座位']
        if AvailableStatus == 'Available':
            return '尚有座位'
        elif AvailableStatus == 'Limited':
            return '座位有限'
        elif AvailableStatus == 'Full':
            return '已無座位'

    # 將車站的json轉成map
    def parseStationJsonToMap(self, station_json_array):
        map = {}
        for json in station_json_array:
            map[json['station_name']] = json['station_id']
        return map

    # 依車站名稱找車站ID
    def findStationIdFromStationName(self, station_name):
        if station_name in self.station_map:
            return self.station_map[station_name]
        return None

    # 查詢指定[車站ID][日期]的站別時刻表資料
    # def queryDailyTimetable(self, StationId, TrainDate):
    #     requestUrl = self.THSR_DailyTimetable %(StationId, TrainDate)
    #     print(requestUrl)
    #     response = requests.get(requestUrl)
    #     print(response.text)


#================ 測試區 ================
# obj = THSRApi()
# obj.queryAllStation()
# obj.queryODFare('1040', '1000')
# obj.qeuryLastestDate()
# obj.queryDailyTimetable_OD('彰化', '台中', obj.qeuryLastestDate()[0])
# obj.compareTime('20:29', '%H:%M')
# obj.queryAvailableSeatStatusList('1040', '152')
# obj.queryNews()