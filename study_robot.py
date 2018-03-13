#!/usr/bin/env python
#encoding: utf8

"""
Created on 2016-7-29

Author: loghyr
Mail:   loghyr@163.com
Tips:   21tb在线学习网站课程学习脚本，自动学习机器人
"""

import os
import sys
import copy
import json
import time
import datetime
import requests
import ConfigParser

reload(sys)
sys.setdefaultencoding('utf-8')

"""conf文件名的定义"""
kConfFileName = "main0.conf"

def log(info):
    """simple log"""
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), info
    sys.stdout.flush()


class Http(object):

    """http client"""
    def __init__(self):
        """init"""
        self.session = requests.Session()
        self.eln_session_id = None
        self.headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36'
                        ' (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        }

    @classmethod
    def instance(cls):
        """
        get instance of this module
        """
        key = "__instance__"
        if hasattr(cls, key):
            return getattr(cls, key)
        else:
            http = Http()
            setattr(cls, key, http)
            return http

    def get_session_id(self):
        """get cookie elsSign, patch it to get/port request param"""
        return self.session.cookies.get('eln_session_id')

    def post(self, api, params=None, json_ret=True):
        """
        send post request
        Params:
            api: request url
            params: dict or just set None
        """
        if not params:
            params = {'elsSign': self.get_session_id()}
        else:
            params.update({'elsSign': self.get_session_id()})
        r = self.session.post(api, params, headers=self.headers)
        if json_ret:
            return r.json()
        return r.text

    def get(self, api, json_ret=True):
        """
        send get request
        Params:
            api: request url
        """
        r = self.session.get(api, params={'elsSign': self.get_session_id()}, headers=self.headers)
        if json_ret:
            return r.json()
        return r.text


class ConfigMgr(object):
    """
    All configuration operation is CRUD by this class
    """
    def __init__(self):
        """
        init
        """
        self._configer = None
        self.work_dir = os.path.dirname(__file__)
        self.config_file = os.path.join(self.work_dir, kConfFileName)

    def init(self):
        """
        load config file
        """
        config_file = self.config_file
        if not os.path.exists(self.config_file):
            raise Exception("config file %s is missing!" % config_file)
        self._configer = ConfigParser.ConfigParser()
        readok = self._configer.read(config_file)
        if config_file not in readok:
            raise Exception("load config file %s failed" % config_file)
        log("load config %s" % config_file)

    def get_section_items(self, section):
        """
        get sepcific section configs in config file as dict
        """
        if self._configer is not None:
            configs = self._configer.items(section)
            return dict(configs)
        raise Exception("config file not loaded")


class Study(object):
    """
    21tb auto study class
    """

    def __init__(self):
        """init"""
        #http client instance
        self.http = Http.instance()
        self.config = ConfigMgr()
        self.config.init()
        self.apis = self.init_api()

    def init_api(self):
        """init api from config"""
        return {
            #登录接口
            'login': self._make_api('login'),
            'save_progress': self._make_api('save_progress'),
            'course_item': self._make_api('course_item'),
            'select_resourse': self._make_api('select_resourse'),
            'select_check': self._make_api('select_check'),
            'update_timestep': self._make_api('update_timestep'),
            'course_show': self._make_api('course_show'),
            'heartbeat': self._make_api('heartbeat'),
            'course_center': self._make_api('course_center'),
            'enter_course': self._make_api('enter_course')
            }

    def _make_api(self, api):
        """gen api full url"""
        apis_conf = self.config.get_section_items('api')
        if api in apis_conf:
            return '%s%s' % (apis_conf['host'], apis_conf[api])
        raise Exception('api:%s is not configed' % apis_conf[api])

    def do_login(self):
        """login"""
        main_conf = self.config.get_section_items('main')
        username = main_conf['username']
        password = main_conf['password']
        corpcode = main_conf['corpcode']
        params = {
            'corpCode': corpcode,
            'loginName': username,
            'password': password,
            'returnUrl': '',
            'courseId': '',
            'securityCode': '',
            'continueLogin': 'true'
            }
        r = self.http.post(self.apis['login'], params=params)
        if self.http.get_session_id():
            log('user:%s login success!' % username)
        else:
            msg = r.get('message')
            raise Exception("You maybe not login success? e:%s" % msg)

    def do_heartbeat(self):
        """heartbeat"""
        try:
            ret = self.http.post(self.apis['heartbeat'], {'_ajax_toKen': 'os'})
            log('do heartbeat, %s' % ret.get('success'))
        except Exception as e:
            log('do heartbeat, %s, ret:%s' % (ret.get('failure'), str(ret)))

    def get_my_course(self):
    	"""getmycourse"""
    	params = {
    		'page.pageSize': '12',
    		'page.sortName': 'STUDYTIME',
            'page.pageNo': '1',
    		'_': int(time.time())
    	    }
    	try:
    		ret = self.http.get(self.apis['course_center'], params)
    		log('获取课程中心成功')
    	except Exception, e:
    		log('获取课程中心失败')
        courseListRaw = ret['rows']
        courseList = []
        for i in courseListRaw:
            if i.get('getScoreTime') is not None:
                continue
            courseList.append(i.get('courseId').encode('utf-8'))
        log('课程中心共有%s门课程未完成' % len(courseList))
        return courseList

    def read_local_studyList(self, course_list):
        """优先学习study.list的课程"""
        if os.path.exists(os.getcwd() + '/' + 'study.list'):
            log("study.list文件存在, 将优先学习")
            prefreList = []
            with open('study.list') as f:
                for course in f:
                    prefreList.append(course.strip().encode('utf-8'))
            prefreList.extend(course_list)
            return prefreList
        else:
            log("study.list文件不存在将直接学习")
            return course_list

    def get_course_items(self, course_id, pretty=False):
        """get course child items"""
        api = self.apis['course_item'] % course_id
        ret_json = self.http.get(api) 
        ret_json = ret_json[0]
        children_list = ret_json['children']
        item_list = []
        for item in children_list:
            if len(item['children']) == 0:
                cell = {}
                cell['name'] = item['text']
                cell['scoId'] = item['id']
                item_list.append(cell)
            else:
                for i in item['children']:
                    cell = {}
                    cell['name'] = i['text']
                    cell['scoId'] = i['id']
                    item_list.append(cell)
        if pretty:
            for i in item_list:
                log('课程名: %s %s' % (i['name'], i['scoId']))
            log('total items:%s' % len(item_list))
        else:
            return item_list

    def select_score_item(self, course_id, score_id):
        """select one scoreitem and do check"""
        params = {'courseId': course_id, 
                  'scoId': score_id, 
                  'firstLoad': 'true'}
        r = self.http.post(self.apis['select_resourse'], params, json_ret=False)
        try:
            location = float(json.loads(r)['location'])
        except:
            location = 0.1
        select_check_api = self.apis['select_check']
        api = select_check_api % (course_id, score_id)
        r = self.http.post(api, json_ret=False)
        return location
 
    def update_timestep(self):
        """update study log to server per 3min"""
        ret = self.http.post(self.apis['update_timestep'])
        log('do updateTimestepByUserTimmer, %s' % ret.strip('"').capitalize())

    def do_save(self, course_id, score_id, location):
        """保存进度条，21tb的服务端会进行校验"""
        params = {
                    'courseId': '',  #课程的id
                    'scoId': '',    #章节的id
                    'progress_measure': '100', #进度 ，这个参数已经不起作用
                    'session_time':'0:0:180',  #在线的时间，这个参数已经不起作用
                    'location': '691.1',   #进度条位置 秒，关键是这个
                    'logId': '',
                    'current_app_id':''
                }
        params.update({'courseId': course_id, 'scoId': score_id, 'location': location})
        r = self.http.post(self.apis['save_progress'], params)
        try:
            if not r:
                params_res = {'courseId': course_id, 'scoId': score_id}
                r = self.http.post(self.apis['select_resourse'], params_res)
                #判断完成条件之2，查询接口
                if r.get('isComplete') == 'true':
                    return True
            info = '\033[91m\tcourseProgress: %s\tcompleteRate:%s\tcompleted:%s\t\033[0m' %\
                         (r.get('courseProgress', '-'), r.get('completeRate'), r.get('completed', '-'))
            log(info)
            #判断完成条件之1，save 返回判断
            if r.get('completed', '-') == 'true':
                return True
        except Exception as e:
            log(e)
            _ = '总进度:', '-', '小节:', '-'
            log('总进度:\t-\t小节:\t-')
        return False


    def study(self, course_id):
        """study one course"""
        time_step = 180
        log('start course:%s' % course_id)
        self.http.post(self.apis['enter_course'] % course_id, json_ret=False)
        course_show_api = self.apis['course_show'] % course_id
        log('url:%s' % course_show_api)
        self.http.post(course_show_api, json_ret=False)
        items_list = self.get_course_items(course_id)
        log('*' * 50)
        log('共有 %s 个子课程' % len(items_list))
        for index, i in enumerate(items_list):
            log('%s、%s ' % (index + 1, i['name']))
        log('*' * 50)
        log('begin to start...')
        for index, i in enumerate(items_list):
            sco_id = i['scoId']
            log('begin to study:%s-%s %s' % (index + 1, i['name'], sco_id))
            location = self.select_score_item(course_id, sco_id)
            cnt = 0
            while True:
                location = location + time_step * cnt
                cnt += 1
                log('location: %s' % location)
                self.do_heartbeat()
                self.update_timestep()
                ret = self.do_save(course_id, sco_id, location)
                if ret:
                    log('%s-%s %s' % (course_id, sco_id, 'done, start next'))
                    break
                log('*********** study %ss then go on *************' % time_step)
                time.sleep(time_step)
        info = '\033[92m\tDONE COURSE, url:%s\033[0m' % course_show_api
        log(info)

    def run(self):
        """入口"""
        s = time.time()
        self.do_login()
        course_list = self.read_local_studyList(self.get_my_course())
        for course_id in course_list:
            try:
                self.study(course_id)
            except Exception as e:
                log("exception occured, study next..")
        cost = int(time.time() - s)
        log('main end, cost: %ss' % cost)


if __name__ == '__main__':
    study = Study()
    study.run()