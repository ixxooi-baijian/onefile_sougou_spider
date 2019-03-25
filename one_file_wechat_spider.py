import requests
from urllib.parse import urlencode
from pyquery import PyQuery as pq
import time
import pandas as pd
import os
import urllib3
#禁用requests安全建议警告，不影响结果
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxiesDB(object):
    def __init__(self, proxies_url):
        self.Proxies = None
        self.Proxies_list = []
        self.Proxies_url = proxies_url

    def get_proxies_func(self):
        if not self.Proxies_list:
            print('\033[1;34;48m{------>开始收集代理ip<------}\033[0m')
            try:
                ip_port_json = requests.get(self.Proxies_url)
                ip_port_json.close()
                for ip_port in ip_port_json.json()['data']['proxy_list']:
                    proxy_whitelist = {"http": "http://{0}".format(ip_port),
                                       "https": "http://{0}".format(ip_port)}
                    self.Proxies_list.append(proxy_whitelist)
                self.Proxies = self.Proxies_list.pop()
                print(self.Proxies)
                return self.Proxies
            except Exception as e:
                print(e)
                print('\033[1;31;48m \n\n\n !!!代理链接失效!!!请自行购买代理后生成api链接后修改Proxies_url!!!\n\n\n \033[0m')
                exit()
        else:
            print('{--->开始更换ip:')
            self.Proxies = self.Proxies_list.pop()
            print(self.Proxies)
            return self.Proxies


class SGWeChatSpider(object):
    def __init__(self, pdb, keyword, ft, et, file_name):
        self.Pdb = pdb
        self.Ft = ft
        self.Et = et
        self.File_name = file_name
        self.Keyword = keyword

        self.Index = 0
        self.Day_second = 86400
        self.Headers = {
            'Host' :'weixin.sogou.com',
            'Connection' :'keep-alive',
            'Cache-Control' :'max-age=0',
            'User-Agent' :'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'Accept' :'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,image/sharpp,image/apng,image/tpg,*/*;q=0.8',
            'Accept-Encoding' :'gzip, deflate',
            'Accept-Language' :'zh-CN,en-US;q=0.8',
            'Referer': 'https://weixin.sogou.com/',
        }
        self.Search_url = None
        self.Proxies = None
        self.Html = None
        self.Page = 1
        self.Retry = 1

        self.init_file()
        self.cheat_server_create_headers()

    def init_file(self):
        if not os.path.exists(self.File_name):
            with open(self.File_name, mode='w', encoding='utf_8_sig') as c:
                c.write('序号,文章标题,文章简述,发文时间,发文公众号')

    def cheat_server_create_headers(self):
        get_data = {
            'type': 2,
            'ie': 'utf8',
            'query': self.Keyword,
        }
        base_url = 'https://weixin.sogou.com/weixin?'
        url = base_url + urlencode(get_data)

        try:
            response = requests.get(url, headers=self.Headers, proxies=self.Proxies, timeout=10, allow_redirects=False,
                                    verify=False)
            response.close()
            if response.status_code == 200:
                self.Headers['Cookie'] = response.headers['Set-Cookie']
                self.Headers['Referer'] = url
                print('\033[1;34;48m 欺骗成功，构建头部成功。\033[0m')
            else:
                print('\033[1;31;48m 欺骗失败。\033[0m')
                self.Proxies = self.Pdb.get_proxies_func()
                self.cheat_server_create_headers()
        except Exception as e:
            print(e)
            self.Proxies = self.Pdb.get_proxies_func()
            self.cheat_server_create_headers()

    def create_search_url(self):
        search_url_base = 'https://weixin.sogou.com/weixin?'
        get_data = {
            'type': 2,
            'ie': 'utf8',
            'query': self.Keyword,
            'tsn': 5,
            'ft': self.Ft,
            'et': self.Ft,
            'page': self.Page,
        }
        self.Search_url = search_url_base + urlencode(get_data)

    def get_html(self):
        self.create_search_url()
        try:
            response = requests.get(self.Search_url, headers=self.Headers, proxies=self.Proxies, allow_redirects=False,
                                    verify=False)
            response.close()
            if response.status_code == 200:
                self.Html = response.text
                self.Retry = 1
                return 1
            else:
                if self.Retry <= 3:
                    self.Proxies = self.Pdb.get_proxies_func()
                    self.cheat_server_create_headers()
                    self.get_html()
                    self.Retry += 1
                else:
                    return 0
        except Exception as e:
            print(e)
            if self.Retry <= 3:
                self.Proxies = self.Pdb.get_proxies_func()
                self.cheat_server_create_headers()
                self.get_html()
            self.Retry += 1

    def parse_html(self):
        result_list = list()
        doc = pq(self.Html)

        txt_box = doc('.news-box .txt-box')
        if txt_box:
            for one in txt_box.items():
                one_list = []
                title = one('h3').text()
                content = one('p').text()
                nickname = one('.s-p').text().split('document')[0]
                date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(one('.s-p .s2').text().split("'")[1])))
                one_list.append(self.Index)
                one_list.append(title)
                one_list.append(content)
                one_list.append(date)
                one_list.append(nickname)
                result_list.append(one_list)
                self.Index += 1

            df = pd.DataFrame(result_list)
            df.to_csv(self.File_name, mode='a', encoding='utf_8_sig', index=False, header=False)
            print('\033[1;34;48m 爬取成功,并保存在文件{1} \033[0m'.format(self.Search_url, self.File_name))
            time.sleep(1.7)
        else:
            if doc('.text-info'):
                print(self.Ft, doc('.text-info').text().split()[1])
                self.Page = 11
            else:
                print(self.Html)
                print('something error but i do not want to deal with it')

    def run(self):
        start_timestamp = time.mktime(time.strptime(self.Ft, '%Y-%m-%d'))
        end_timestamp = time.mktime(time.strptime(self.Et, '%Y-%m-%d'))
        while end_timestamp > start_timestamp:
            self.Page = 1
            self.Ft = time.strftime('%Y-%m-%d', time.localtime(start_timestamp))
            while self.Page <= 10:
                flag = self.get_html()
                if flag == 1:
                    self.parse_html()
                    self.Page += 1
                else:
                    self.Page += 1
                    print('\033[1;31;48m 已经尝试重试了三次爬取，任未成功，舍弃爬取:{0} \033[0m'.format(self.Search_url))
            start_timestamp = start_timestamp + self.Day_second


if __name__ == '__main__':
    # 代理链接，下面这个是我个人购买的的代理，失效时间：2019-03-28，失效后请自行购买
    Proxies_url = 'https://dev.kdlapi.com/api/getproxy/?orderid=915347983890999&num=20&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=2&method=2&an_an=1&an_ha=1&sp1=1&quality=1&format=json&sep=1'
    # 要爬取的关键字
    Keyword = '优惠'
    # 爬取开始日期
    Ft = '2019-01-01'
    # 结束日期默认当日，若需要自定义请仿造Ft个格式输入，如：Et = '2019-03-25'
    Et = time.strftime('%Y-%m-%d', time.localtime())
    # 保存到的文件名称,仅允许保存为csv数据，否者报错不负责
    File_name = 'sg_wc_data.csv'

    Pdb = ProxiesDB(Proxies_url)
    main_spider = SGWeChatSpider(pdb=Pdb, keyword=Keyword, ft=Ft, et=Et, file_name=File_name)
    main_spider.run()
