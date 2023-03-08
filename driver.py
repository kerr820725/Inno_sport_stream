from selenium import webdriver
import  os , requests ,zipfile ,sys
from Logger import create_logger

class Driver:# 開啟 webdrvier 的所有流程
    def __init__(self):
        self.log =  create_logger()
        

    def get_Chrome_version(self):#取得local Chrome version
        import winreg # docekr 的 無法支援
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Google\Chrome\BLBeacon')
        version, types  = winreg.QueryValueEx(key, 'version')
        local_version = version.split('.')[0]
        self.log.info('local Chrome version : %s'%local_version)
        return local_version


    def get_Driver_version(self):# 取得 local 的 chromedriver version
        try:
            local_driver_version = os.popen('chromedriver --version').read().split(' ')[1].split('.')[0]
            self.log.info('local driver version : %s'%local_driver_version)
            return local_driver_version
        except:# Local 沒有 chromedriver
            self.log.info('local 找不到 chromedriver , 需線上下載')
            return 'False'
    
    
    def get_server_chrome_versions(self, version):# 抓取線上 driver 網站 , 並帶入 指定的 driver version
        try:
            url="https://registry.npmmirror.com/-/binary/chromedriver/"#線上 driver 網站
            rep = requests.get(url).json()# list 裡麵包字典
        except:
            self.log.error('線上 driver Url 取得有誤 ,需確認')
            return False
        
        
        for dict_ in rep:
            split_version = dict_['name'].split('.')[0]# # 抓取 name 並把 他取出 70.0.3538.97/ > 70
            if version == split_version:
                down_url = dict_['url']
                self.log.info('抓到 對應的 driver 版本 : %s'%dict_['name'])
                return down_url + 'chromedriver_win32.zip'


    def download_driver(self, download_url):# 下載 driver 到local 方法 
    
        file = requests.get(download_url)
        with open("chromedriver.zip", 'wb') as zip_file:
            zip_file.write(file.content)
        self.log.info('新driver 下载成功')


    def unzip_driver(self):# 下載完後 解壓縮 到本地專案裡
        '''解压Chromedriver压缩包到指定目录'''
        f = zipfile.ZipFile("chromedriver.zip",'r')
        for file in f.namelist():
            f.extract(file, '.')
        self.log.info('解壓縮成功')


    def return_driver(self , index=0):# 開啟 webdriver 
        '''
        流程 : 先取得 本地  chrome / chromedriver version
        如果沒有 chromerdriver 或者  版本比 chrome version 低 , 就會先上 抓取 對應的 chromedriver 版本
        '''

        if sys.platform == 'win32':
            driver_path =  'chromedriver.exe'
            if index == 0:
                local_chrome_version = self.get_Chrome_version()
                local_driver_version = self.get_Driver_version()
                if local_chrome_version == local_driver_version:
                    self.log.info('local chrome version 和 driver version 一致 , 無須 下載')
                else:
                    down_url = self.get_server_chrome_versions(version = local_chrome_version)
                    if down_url is False: # 線上下載 url 有誤
                        return False
                    self.download_driver(down_url)
                    self.unzip_driver()

                return True
        else:# docker
            driver_path =  '/usr/local/bin/chromedriver'
            if index == 0:
                return True


        chrome_options = webdriver.ChromeOptions()
        

        chrome_options.add_argument("--headless") #無頭模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("log-level=3")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--incognito")# 無痕
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36')



        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation','enable-logging'])
        dr = webdriver.Chrome(chrome_options=chrome_options , executable_path=  driver_path )
        dr.set_page_load_timeout(50)
        return dr