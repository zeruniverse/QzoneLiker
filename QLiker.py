# -*- coding: utf-8 -*-

import re
import random
import json
import os
import sys
import datetime
import time
import threading
import logging
import urllib
from HttpClient import HttpClient

reload(sys)
sys.setdefaultencoding("utf-8")

# CONFIGURATION FIELD
checkFrequency = 5
#check every k seconds
# STOP EDITING HERE
HttpClient_Ist = HttpClient()
UIN = 0
Referer = 'http://user.qzone.qq.com/'
QzoneLoginUrl = 'http://xui.ptlogin2.qq.com/cgi-bin/xlogin?proxy_url=http%3A//qzs.qq.com/qzone/v6/portal/proxy.html&daid=5&pt_qzone_sig=1&hide_title_bar=1&low_login=0&qlogin_auto_login=1&no_verifyimg=1&link_target=blank&appid=549000912&style=22&target=self&s_url=http%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&pt_qr_app=%E6%89%8B%E6%9C%BAQQ%E7%A9%BA%E9%97%B4&pt_qr_link=http%3A//z.qzone.com/download.html&self_regurl=http%3A//qzs.qq.com/qzone/v6/reg/index.html&pt_qr_help_link=http%3A//z.qzone.com/download.html'

initTime = time.time()


logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
def getAbstime():
    return int(time.time())
    
def date_to_millis(d):
    return int(time.mktime(d.timetuple())) * 1000

def getReValue(html, rex, er, ex):
    v = re.search(rex, html)

    if v is None:
        logging.error(er)

        if ex:
            raise Exception, er
        return ''

    return v.group(1)
    
# -----------------
# 登陆
# -----------------
class Login(HttpClient):
    MaxTryTime = 5

    def __init__(self, vpath, qq=0):
        global UIN, Referer
        self.VPath = vpath  # QRCode保存路径
        AdminQQ = int(qq)
        logging.critical("正在获取登陆页面")
        self.setCookie('_qz_referrer','qzone.qq.com','qq.com')
        self.Get(QzoneLoginUrl,'http://qzone.qq.com/')
        StarTime = date_to_millis(datetime.datetime.utcnow())
        T = 0
        while True:
            T = T + 1
            self.Download('http://ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&daid=5', self.VPath)
            LoginSig = self.getCookie('pt_login_sig')
            logging.info('[{0}] Get QRCode Picture Success.'.format(T))           
            while True:
                html = self.Get('http://ptlogin2.qq.com/ptqrlogin?u1=http%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-{0}&js_ver=10131&js_type=1&login_sig={1}&daid=5&pt_qzone_sig=1'.format(date_to_millis(datetime.datetime.utcnow()) - StarTime, LoginSig), QzoneLoginUrl)
                # logging.info(html)
                ret = html.split("'")
                if ret[1] == '65' or ret[1] == '0':  # 65: QRCode 失效, 0: 验证成功, 66: 未失效, 67: 验证中
                    break
                time.sleep(2)
            if ret[1] == '0' or T > self.MaxTryTime:
                break

        logging.info(ret)
        if ret[1] != '0':
            return
        logging.critical("二维码已扫描，正在登陆")
        
        # 删除QRCode文件
        if os.path.exists(self.VPath):
            os.remove(self.VPath)

        # 记录登陆账号的昵称
        tmpUserName = ret[11]

        self.Get(ret[5])
        UIN = getReValue(ret[5], r'uin=([0-9]+?)&', 'Fail to get QQ number', 1)
        Referer = Referer+str(UIN)




def utf8_unicode(c):            
    if len(c)==1:                                 
        return ord(c)
    elif len(c)==2:
        n = (ord(c[0]) & 0x3f) << 6              
        n += ord(c[1]) & 0x3f              
        return n        
    elif len(c)==3:
        n = (ord(c[0]) & 0x1f) << 12
        n += (ord(c[1]) & 0x3f) << 6
        n += ord(c[2]) & 0x3f
        return n
    else:                
        n = (ord(c[0]) & 0x0f) << 18
        n += (ord(c[1]) & 0x3f) << 12
        n += (ord(c[2]) & 0x3f) << 6
        n += ord(c[3]) & 0x3f
        return n

def getGTK(skey):
    hash = 5381
    for i in range(0,len(skey)):
        hash += (hash << 5) + utf8_unicode(skey[i])
    return hash & 0x7fffffff

def MsgHandler(tuin, content, isSess, group_sig, service_type):
    if isSess == 0:
        reqURL = "http://d.web2.qq.com/channel/send_buddy_msg2"
        data = (
            ('r', '{{"to":{0}, "face":594, "content":"[\\"{4}\\", [\\"font\\", {{\\"name\\":\\"Arial\\", \\"size\\":\\"10\\", \\"style\\":[0, 0, 0], \\"color\\":\\"000000\\"}}]]", "clientid":"{1}", "msg_id":{2}, "psessionid":"{3}"}}'.format(tuin, ClientID, msgId, PSessionID, str(content.replace("\\", "\\\\\\\\").replace("\n", "\\\\n").replace("\t", "\\\\t")).decode("utf-8"))),
            ('clientid', ClientID),
            ('psessionid', PSessionID)
        )
        rsp = HttpClient_Ist.Post(reqURL, data, Referer)
        rspp = json.loads(rsp)
        if rspp['retcode']!= 0:
            logging.error("reply pmchat error"+str(rspp['retcode']))
    




class check_msg(threading.Thread):
    # try:
    #   pass
    # except KeybordInterrupt:
    #   try:
    #     user_input = (raw_input("回复系统：（输入格式:{群聊2or私聊1}, {群号or账号}, {内容}）\n")).split(",")
    #     if (user_input[0] == 1):

    #       for kv in self.FriendList :
    #         if str(kv[1]) == str(user_input[1]):
    #           tuin == kv[0]

    #       self.send_msg(tuin, user_input[2])

    #   except KeybordInterrupt:
    #     exit(0)
    #   except Exception, e:
    #     print Exception, e

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global PTWebQQ
        E = 0
        # 心跳包轮询
        while 1:
            if E > 5:
                break
            try:
                ret = self.check()
            except:
                E += 1
                continue
            # logging.info(ret)

            # 返回数据有误
            if ret == "":
                E += 1
                continue

            # POST数据有误
            if ret['retcode'] == 100006:
                break

            # 无消息
            if ret['retcode'] == 102:
                E = 0
                continue

            # 更新PTWebQQ值
            if ret['retcode'] == 116:
                PTWebQQ = ret['p']
                E = 0
                continue

            if ret['retcode'] == 0:
                # 信息分发
                msg_handler(ret['result'])
                E = 0
                continue

        logging.critical("轮询错误超过五次")

    # 向服务器查询新消息
    def check(self):

        html = HttpClient_Ist.Post('http://d.web2.qq.com/channel/poll2', {
            'r': '{{"ptwebqq":"{1}","clientid":{2},"psessionid":"{0}","key":""}}'.format(PSessionID, PTWebQQ, ClientID)
        }, Referer)
        logging.info("Check html: " + str(html))
        try:
            ret = json.loads(html)
        except Exception as e:
            logging.error(str(e))
            logging.critical("Check error occured, retrying.")
            return self.check()

        return ret


class pmchat_thread(threading.Thread):

    
    # con = threading.Condition()
    # newIp = ''

    def __init__(self, tuin, isSess, group_sig, service_type):
        threading.Thread.__init__(self)
        self.tuin = tuin
        self.isSess = isSess
        self.group_sig=group_sig
        self.service_type=service_type
        self.tqq = uin_to_account(tuin)
        self.lastcheck = time.time()
        self.lastseq=0
        self.replystreak = 0
        logging.info("私聊线程生成，私聊对象："+str(self.tqq))
    def check(self):
        self.lastcheck = time.time()
    def run(self):
        while 1:
            time.sleep(199)
            if time.time() - self.lastcheck > 300:
                break

    def reply(self, content):
        send_msg(self.tuin, str(content), self.isSess, self.group_sig, self.service_type)
        logging.info("Reply to " + str(self.tqq) + ":" + str(content))

    def push(self, ipContent, seq):
        if seq == self.lastseq:
            return True
        else:
            self.lastseq=seq
        #防止机器人对聊
        if self.replystreak>30:
            self.replystreak = 0
            return True
        try:
            self.replystreak = self.replystreak + 1
            logging.info("PM get info from AI: "+ipContent)
            paraf={ 'userid' : str(self.tqq), 'key' : tulingkey, 'info' : ipContent}
            info = HttpClient_Ist.Get('http://www.tuling123.com/openapi/api?'+urllib.urlencode(paraf))
            logging.info("AI REPLY:"+str(info))
            info = json.loads(info)
            if info["code"] in [40001, 40003, 40004]:
                self.reply("我今天累了，不聊了")
                logging.warning("Reach max AI call")
            elif info["code"] in [40002, 40005, 40006, 40007]:
                self.reply("我遇到了一点问题，请稍后@我")
                logging.warning("PM AI return error, code:"+str(info["code"]))
            else:
                rpy = str(info["text"]).replace('<主人>','你').replace('<br>',"\n")
                self.reply(rpy)
            return True
        except Exception, e:
            logging.error("ERROR:"+str(e))
        return False
        


class group_thread(threading.Thread):
    last1 = ''
    lastseq = 0
    replyList = {}
    followList = []

    # 属性
    repeatPicture = False

    def __init__(self, guin):
        threading.Thread.__init__(self)
        self.guin = guin
        self.gid = GroupList[guin]
        self.load()
        self.lastreplytime=0

    def learn(self, key, value, needreply=True):
        if key in self.replyList:
            self.replyList[key].append(value)
        else:
            self.replyList[key] = [value]

        if needreply:
            self.reply("我记住" + str(key) + "的回复了")
            self.save()

    def delete(self, key, value, needreply=True):
        if key in self.replyList and self.replyList[key].count(value):
            self.replyList[key].remove(value)
            if needreply:
                self.reply("我已经不会说" + str(value) + "了")
                self.save()

        else:
            if needreply:
                self.reply("没找到你说的那句话哦")

    def reply(self, content):
        if time.time() - self.lastreplytime < 3.0:
            logging.info("REPLY TOO FAST, ABANDON："+content)
            return False
        self.lastreplytime = time.time()
        reqURL = "http://d.web2.qq.com/channel/send_qun_msg2"
        data = (
            ('r', '{{"group_uin":{0}, "face":564,"content":"[\\"{4}\\",[\\"font\\",{{\\"name\\":\\"Arial\\",\\"size\\":\\"10\\",\\"style\\":[0,0,0],\\"color\\":\\"000000\\"}}]]","clientid":"{1}","msg_id":{2},"psessionid":"{3}"}}'.format(self.guin, ClientID, msgId, PSessionID, str(content.replace("\\", "\\\\\\\\").replace("\n", "\\\\n").replace("\t", "\\\\t")).decode("utf-8"))),
            ('clientid', ClientID),
            ('psessionid', PSessionID)
        )
        logging.info("Reply package: " + str(data))
        rsp = HttpClient_Ist.Post(reqURL, data, Referer)
        try:
            rspp = json.loads(rsp)
            if rspp['retcode'] == 0:         
                logging.info("[Reply to group " + str(self.gid) + "]:" + str(content))
                return True
        except:
            pass
        logging.error("[Fail to reply group " + str(self.gid)+ "]:" + str(rsp))
        return rsp

    def handle(self, send_uin, content, seq):
        # 避免重复处理相同信息
        if seq != self.lastseq:
            pattern = re.compile(r'^(?:!|！)(learn|delete) {(.+)}{(.+)}')
            match = pattern.match(content)
            if match:
                if match.group(1) == 'learn':
                    self.learn(str(match.group(2)).decode('UTF-8'), str(match.group(3)).decode('UTF-8'))
                    logging.debug(self.replyList)
                if match.group(1) == 'delete':
                    self.delete(str(match.group(2)).decode('UTF-8'), str(match.group(3)).decode('UTF-8'))
                    logging.debug(self.replyList)

            else:
                # if not self.follow(send_uin, content):
                #     if not self.tucao(content):
                #         if not self.repeat(content):
                #             if not self.callout(content):
                #                 pass
                if self.aboutme(content):
                    return
                if self.deleteall(content):
                    return
                if self.callout(send_uin, content):
                    return
                if self.follow(send_uin, content):
                    return
                if self.tucao(content):
                    return
                if self.repeat(content):
                    return
                
        else:
            logging.warning("message seq repeat detected.")
        self.lastseq = seq

    def tucao(self, content):
        for key in self.replyList:
            if str(key) in content and self.replyList[key]:
                rd = random.randint(0, len(self.replyList[key]) - 1)
                self.reply(self.replyList[key][rd])
                logging.info('Group Reply'+str(self.replyList[key][rd]))
                return True
        return False

    def repeat(self, content):
        if self.last1 == str(content) and content != '' and content != ' ':
            if self.repeatPicture or "[图片]" not in content:
                self.reply(content)
                logging.info("已复读：{" + str(content) + "}")
                return True
        self.last1 = content
        
        return False

    def follow(self, send_uin, content):
        pattern = re.compile(r'^(?:!|！)(follow|unfollow) (\d+|me)')
        match = pattern.match(content)

        if match:
            target = str(match.group(2))
            if target == 'me':
                target = str(uin_to_account(send_uin))

            if match.group(1) == 'follow' and target not in self.followList:
                self.followList.append(target)
                self.reply("正在关注" + target)
                return True
            if match.group(1) == 'unfollow' and target in self.followList:
                self.followList.remove(target)
                self.reply("我不关注" + target + "了！")
                return True
        else:
            if str(uin_to_account(send_uin)) in self.followList:
                self.reply(content)
                return True
        return False

    def save(self):
        try:
            with open("database."+str(self.gid)+".save", "w+") as savefile:
                savefile.write(json.dumps(self.replyList))
                savefile.close()
        except Exception, e:
            logging.error("写存档出错："+str(e))
    def load(self):
        try:
            with open("database."+str(self.gid)+".save", "r") as savefile:
                saves = savefile.read()
                if saves:
                    self.replyList = json.loads(saves)
                savefile.close()
        except Exception, e:
            logging.info("读取存档出错:"+str(e))
    
    def callout(self, send_uin, content):
        pattern = re.compile(r'^(?:!|！)(ai) (.+)') 
        match = pattern.match(content)
        try:
            if match:
                logging.info("get info from AI: "+str(match.group(2)).decode('UTF-8'))
                usr = str(uin_to_account(send_uin))
                paraf={ 'userid' : usr+'g', 'key' : tulingkey, 'info' : str(match.group(2)).decode('UTF-8')}
                
                info = HttpClient_Ist.Get('http://www.tuling123.com/openapi/api?'+urllib.urlencode(paraf))
                logging.info("AI REPLY:"+str(info))
                info = json.loads(info)
                if info["code"] in [40001, 40003, 40004]:
                    self.reply("我今天累了，不聊了")
                    logging.warning("Reach max AI call")
                elif info["code"] in [40002, 40005, 40006, 40007]:
                    self.reply("我遇到了一点问题，请稍后@我")
                    logging.warning("AI return error, code:"+str(info["code"]))
                else:
                    self.reply(str(info["text"]).replace('<主人>','你').replace('<br>',"\n"))
                return True
        except Exception, e:
            logging.error("ERROR"+str(e))
        return False
        
    def aboutme(self, content):
        pattern = re.compile(r'^(?:!|！)(about)') 
        match = pattern.match(content)
        try:
            if match:
                logging.info("output about info")
                info="小黄鸡3.3 By Jeffery, 源代码：(github.com/zeruniverse/QQRobot)\n使用语法： （按优先级排序，若同时触发则只按优先级最高的类型回复。注意所有!均为半角符号，即英文!）\n\n1.帮助（关于）,输入!about，样例：\n!about\n\n2.智能鸡：输入!ai (空格)+问题，小黄鸡自动回复，举例：\n!ai 你是谁？\n\n3.随从鸡：输入!follow QQ号，小黄鸡会重复发送该QQ号所有发送内容，如对自己使用可以直接使用!follow me，举例：\n!follow 123456789\n!follow me\n取消复读则输入!unfollow QQ(或me),举例：\n!unfollow 123456789\n!unfollow me\n\n4.学习鸡：使用!learn {A}{B}命令让小黄鸡学习，以后有人说A的时候小黄鸡会自动说B。!learn后面有空格，全部符号均为半角（英文），例如\n!learn {你是谁}{我是小黄鸡}\n删除该记录则\n!delete {你是谁}{我是小黄鸡}\n一次删除所有记录使用：\n!deleteall\n\n6.复读鸡：当群里连着两次出现同样信息时复读一遍\n\n\n私戳小黄鸡可以私聊，私聊无格式，全部当智能鸡模式处理。"
                self.reply(info)
                return True
        except Exception, e:
            logging.error("ERROR"+str(e))
        return False
        
    def deleteall(self, content):
        pattern = re.compile(r'^(?:!|！)(deleteall)') 
        match = pattern.match(content)
        try:
            if match:
                logging.info("Delete all learned data for group:"+str(self.gid))
                info="已删除所有学习内容"
                self.replyList.clear()
                self.save()
                self.reply(info)
                return True
        except Exception, e:
            logging.error("ERROR:"+str(e))
        return False
# -----------------
# 主程序
# -----------------

if __name__ == "__main__":
    vpath = './v.jpg'
    qq = 0
    if len(sys.argv) > 1:
        vpath = sys.argv[1]
    if len(sys.argv) > 2:
        qq = sys.argv[2]

    try:
        pass_time()
        qqLogin = Login(vpath, qq)
    except Exception, e:
        logging.critical(str(e))
        os._exit()
    t_check = check_msg()
    t_check.setDaemon(True)
    t_check.start()
    try:        
        with open('groupfollow.txt','r') as f:
            for line in f:
                GroupWatchList += line.strip('\n').split(',')
            logging.info("关注:"+str(GroupWatchList))
    except Exception, e:
        logging.error("读取组存档出错:"+str(e))
            
                
    t_check.join()
