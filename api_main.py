from commom import Env
from Logger import create_logger
import configparser  , os , glob , shutil ,time
import requests  , datetime
import pysftp
from driver import Driver 
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from pathlib import Path
import pytz ,sys




class Sport_Stream(Env):
    def __init__(self):
        super().__init__()
        self.log = create_logger()# log 
        self.config = self.retrun_config()# 取得config 值
        self.site = self.config['site']#平台
        self.env = self.config['env']#環境
        self.sport_list = [1,2,3,4] if self.config['sport_item'] == 'all' else  [self.config['sport_item']]    #運動
        self.inplay_list = ['True' , 'early' ,'today']  if self.config['inplay_list'] == 'all' else  [self.config['inplay_list']]    # 滾球 / 早盤 / 今日
        self.isDebug =  self.config['isDebug']# 0 local / 1 remote
        self.session = requests.Session()
        self.sport_api_URL =  self.env_dict[self.site][self.env]["sport_api_URL"]
        self.platform_URL = self.env_dict[self.site][self.env]["platform_URL"]
        self.headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
            'Referer': self.platform_URL ,
            'Time-Zone': 'GMT+8',
            'accept-language': 'zh-cn'# hardcode簡中
        }
        self.data_table = { 'index': [],'sport':[] , 'iid': [] , 'Inplay': [ ] ,  'tnName': [ ] ,  'name': [ ] ,   'Check Time': []  ,'Kickoff Time': [] ,
        'gifs':[]  , 'mid': [] , 'source': [], 'stream url': [] ,   'Result': [] , 'Reason': [] ,'Screenshot': [] }# 存放每一筆 iid 測項的資料 ,最後把資料 轉給 html使用
        self.current_folder =  datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')+ '_files'

        self.linework_data = {'滾球': {'count':[] , 'error_count': [] } , '早盤': {'count':[] , 'error_count': [] } 
            , '今日': {'count':[] , 'error_count': [] } 
        }# 用來送出 linework訊息 , true: 滾球 , false: 早盤 , today: 今日

        self.report_data = {'足球-滾球':  {'count':[] , 'error_count': [] } ,  '籃球-滾球': {'count':[] , 'error_count': [] } , '網球-滾球': {'count':[] , 'error_count': [] } , 
            '棒球-滾球': {'count':[] , 'error_count': [] }, 
            '足球-今日': {'count':[] , 'error_count': [] }  , '籃球-今日': {'count':[] , 'error_count': [] }  , '網球-今日':  {'count':[] , 'error_count': [] } , 
            '棒球-今日':  {'count':[] , 'error_count': [] }, 
            '足球-早盤': {'count':[] , 'error_count': [] } ,  '籃球-早盤' : {'count':[] , 'error_count': [] }  , '網球-早盤': {'count':[] , 'error_count': [] } , 
            '棒球-早盤': {'count':[] , 'error_count': [] } , 
        }#用來 給報告顯示  

        try:# 有沒有建立過
            os.mkdir('report')
        except:
            pass
        os.mkdir( 'report/' + self.current_folder )

        #建立 此次的report html
        myfile = Path('report/%s/report.html'%self.current_folder)
        myfile.touch(exist_ok=True)
        f = open(myfile)

        self.all_count = 0# 此次 執行的所有比數
        

    def retrun_config(self):
        config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
        config.read('config.ini', encoding="utf-8")
        config = config['config']

        return config 

    def return_report_data(self): #給報告顯示的結果 
        report_dict = {}
        self.log.info('self.report_data: %s'%self.report_data )
        for key , value in self.report_data.items():# key 為 今日/　早盤 /滾球
            if value['count']: # 有可能會有無賽事 , list會是空
                error_count = value['error_count'][0]
                count = value['count'][0]

                precent = round(( int(error_count)/int( count) )*100 ,2)
                precent_format = f'{error_count}/{count} = {precent}%'


            else:# 無賽事
                precent_format = f'0/0 = 0.0%'

            report_dict[  key ] = precent_format# 回傳 { [滾球]:   失敗率訊息 } 
        
        self.log.info('report_dict : %s'%report_dict)
        return report_dict


    def return_lineWork_msg(self):# 回傳  訊息 結構
        msg_dict = {}
        self.log.info('self.linework_data: %s'%self.linework_data )
        for key,value in self.linework_data.items():# key 為 今日/　早盤 /滾球
            if value['count']: # 有可能會有無賽事 , list會是空 
                error_count = sum(value['error_count'])# 這邊會是 所有運動的list
                count =  sum(value['count'])

                precent = round(( int(error_count)/int( count) )*100 ,2)
                precent_format = f'{precent}'
                case_msg = "失敗率: %s/%s = %s "%(error_count , count ,  precent_format) + "%"
            
                msg_dict[  '[%s]'%key ] = case_msg# 回傳 { [滾球]:   失敗率訊息 } 
        
        return msg_dict



    def write_config(self , sport_key, msg):# 寫入 每次測試 的case的訊息 

        config = configparser.RawConfigParser(comment_prefixes='/', allow_no_value=True)
        #config['send_msg'] = {'result': msg}
        config.read('config.ini', encoding='utf-8')

        config.set('Sport_msg', sport_key , msg)


        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    
    '''
    def Allure_image(self , browser):#預設使用 時間訊息

        pic_msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        allure.attach(browser.get_screenshot_as_png(), pic_msg , allure.attachment_type.PNG)
    '''

    def delete_images(self):# 會刪除 不是今天生成 的資料夾 日期
        today_ = datetime.datetime.now().strftime('%Y-%m-%d')

        py_files = glob.glob('./report/*_files')
        self.log.info(py_files)
        for py_file in py_files:
            if today_ in py_file:
                continue
            try:
                shutil.rmtree(py_file)
            except OSError as e:
                self.log.info(f"Error:{ e.strerror}")


    def getImage(self, driver , pic_name ):
      
        #會分兩個 變數 .是因為 report 的路徑 和 此檔案路徑 不同 , screen_name 是給 html要抓的路徑
        try:

            repot_screen = 'report/%s/%s.png'%(self.current_folder , pic_name)
            screen_name = '%s.png'%(pic_name )

            #self.screen = driver.get_screenshot_as_base64()
            driver.save_screenshot(repot_screen) 
            self.data_table['Screenshot'].append(screen_name)
        except Exception as e:
            self.log.error('getImage : %s'%e)



    def sendlineworks( self , accountID, roomID, message):
        payload = {
            "content": {
                "type": "text",
                "message": message
            }
        }
        if roomID != "":
            payload['roomID'] = roomID
        elif accountID != "":
            payload['accountID'] = accountID


        if self.isDebug == '0':# local
            qa_lineworks_ip = "172.28.40.57:9001"
        else:
            qa_lineworks_ip = "172.19.0.4:9000"

        qa_lineworks_ip = '172.28.10.136:9000/'
    
        try:
            r = requests.request("POST", url=f'http://{qa_lineworks_ip}/sendmsg', json=payload)
            return r
        except Exception as e:
            self.log.error('sendlineworks linework : %s'%e)
            return False

    def sftp_(self):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            sHostName = '172.28.40.61'
            sUserName = 'ubuntu'
            sPassWord = 'ubuntu'

            
            with pysftp.Connection(sHostName, username=sUserName, password=sPassWord, cnopts=cnopts) as sftp:
                to_dir = '/var/www/html/sport_stream_check'
  
                sftp.cwd(to_dir)
                '''
                不在程式裡  刪除報告
                today_ = datetime.datetime.now().strftime('%Y-%m-%d')
                for file_name in sftp.listdir():# 刪除 不是今天 產出的 資料夾
                    if today_ not in file_name:
                        sftp.execute('rm -rf %s/%s'%(to_dir, file_name ) )
                '''

                from_dir =  os.path.normpath(os.getcwd() + '/report')
                for _root, _dirs, _files in os.walk(from_dir):
                    for f in _files:
                        _folder = ".{}".format(_root.split(from_dir)[1].replace('\\','/'))
                        try:
                            sftp.mkdir(_folder)
                        except Exception as error:
                            pass
                        else:
                            pass
                        fileName = os.path.join(_root, f).replace('\\', '/')
                        sftp.put(fileName, "./{}/{}".format(_folder, f), preserve_mtime=True)
        except Exception as e:
            self.log.error('sftp_: %s'%e)
            return False
  



    def odds_send_msg( self , sid , iid ,tnName , name   , run_inplay , kickoffTime , Failmsg):# 每個iid loop出來 有錯誤的訊息寄出

        msg = "環境: %s - %s"%(self.site , self.env) +  "\n\n"

        msg += "sid:"+str(sid) + "\n"
        msg += "iid: "+str(iid) + "\n\n"
        msg += "Inplay: "+ str(run_inplay) +    " , 開賽時間: "+ str(kickoffTime)   +  "\n"
        msg += "聯賽名稱: "+ tnName + "\n"
        msg += "賽事名稱: "+ name + "\n\n"
        #msg += "mid: %s  ,gifMid: %s "%(bmid , gifMid) + "\n"
        msg += "錯誤原因: %s "%Failmsg + "\n"


        self.sendlineworks("nicole0159@myworks", "118475617", msg)
        #self.sendlineworks("nicole0159@myworks", "112575287", msg)
        

    def send_summery_msg(self):
        
        sport_msg = self.return_lineWork_msg()# 回傳   此次執行的  檢查筆數 : 失敗筆數 ,key  為 運動 /早盤or滾球

        msg =  "動態圖自動化檢查內容: " + "\n"
        msg += "環境: %s - %s"%(self.site , self.env) +  "\n"
        msg += "檢查總筆數: %s"%(self.all_count) +  "\n\n"

        for key,value in sport_msg.items():
            msg +=f"{key}" + "\n"
            msg += f"{value}" + "\n"
            msg += "---------------------------------" +"\n\n"

        msg += "詳細資訊請參考  http://172.28.40.61/sport_stream_check/%s/report.html"%self.current_folder
        self.sendlineworks("nicole0159@myworks", "118475617", msg) # 自己AT
        #self.sendlineworks("nicole0159@myworks", "112575287", msg)

    def send_error_msg(self , msg):
        all_msg =  "動態圖自動化檢查內容: " + "\n"
        all_msg += "環境: %s - %s"%(self.site , self.env) +  "\n\n"
        all_msg += msg 
        self.sendlineworks("nicole0159@myworks", "118475617", all_msg)

    def sport_tournaments(self , sid = 1 , inplay= True):# 取得 運動 , 滾球/早盤 的相關 iid  
        self.sport_name = self.sport_item[str(sid) ]
        try:
            if inplay == 'True' :# 滾球
                url =  f"{self.sport_api_URL}/business/sport/tournament/info?sid={sid}&inplay=true&sort=tournament"#滾球
                datelist = ['']# 給一個假值 
                self.inplay = 'true'
                self.play_type = '滾球'
            else: # 早盤 或這今日 , 先取得 相關 支援的日期
                if inplay == 'early':
                    platform_api_URL = self.env_dict[self.site][self.env]["platform_api_URL"]# -> https://tiger-api.innostg.site/product
                    date_url = f"{ platform_api_URL }/business/sport/prematch/datelist?sid={sid}"
                    response = self.session.get( date_url, headers=self.headers).json()
                    datelist = response['data']['dateList'][:7]# list 取出 7天的
                    datelist = list(map(lambda x: x.replace('-','') ,datelist ))# 把 date list , 全部 2022-07-28 -> 20220728
                    self.log.info('datelist: %s'%datelist)
                    self.inplay = 'false'
                    self.play_type = '早盤'
                
                else:# 今日
                    self.inplay = 'today'
                    self.play_type = '今日'
                    datelist = ['today']# 給一個假值

                url =  f"{self.sport_api_URL }/business/sport/tournament/info?sid={sid}&inplay=false&sort=tournament&date="#早盤 ,下面日期 會在 loop datelist 加進來


        except Exception as e:
            self.log.error('sport_tournament error : %s'%e)
            return False
            
            
        self.tournament_detail = {}# key 為 iid , value 為 vd的值
        self.tournament_name = {} #key 為iid  , value 放 name / tnName ,用來 告警給 sport_match  失敗訊息用 
        for date in datelist:
            try:
                r = self.session.get(url = url + date ,  headers=self.headers ).json()

                for tournament in r['data']['tournaments'] :
                    for match_detail in tournament['matches']:
                        if str(sid) == '4' and  match_detail['tnName'] != '美国职业棒球大联盟': # 棒球只檢查  美国职业棒球大联盟
                            continue

                        new_list = []
                        new_list.append(  match_detail['name'] )
                        new_list.append(  match_detail['tnName'] )
                        self.tournament_detail[match_detail['iid']  ] = match_detail['vd']
                        
                        self.tournament_name[ str(match_detail['iid'])   ] = new_list



            
            except Exception as e:
                self.log.error('sport_tournaments : %s ,  error: %s'%(r ,e )  )


        if self.tournament_detail:# 正常會走這
            return True
        
        return False


    def sport_match(self , sid= 1):# 將 self.tournament_detail 的 iid 值loop出來  打  business/sport/inplay/match?sid=&iid=&vd= 
        
        count = 0
        error_count = 0
        #Fail_all_msg = "\n"# 這是會延展 此次case的所有錯誤訊息顯示在報告上 , Failmsg會是每個loop錯誤訊息 寄到 linework

        vendor_id = self.env_dict[self.site]["vendor_id"]
        
        dr =  Driver().return_driver(index = 1)# index 帶不是 0 ,不會去做 確認 環境問題
        if self.inplay == 'true':
            inplay_url  =  f"{self.sport_api_URL }/business/sport/inplay/match?"
        else:
            inplay_url  =  f"{self.sport_api_URL }/business/sport/prematch/match?"

        
        

        
        #with allure.step('%s'%self.play_type):
        for iid , vd in self.tournament_detail.items():
            self.all_count += 1
            self.data_table['index'].append(str(self.all_count))
            self.data_table['sport'].append(self.sport_name ) 
            self.data_table['iid'].append(str(iid))
            self.data_table['Inplay'].append(self.play_type)
            tw = pytz.timezone('Asia/Taipei')
            self.data_table['Check Time'].append( datetime.datetime.now().astimezone(tw).strftime('%Y-%m-%d %H:%M:%S')  )
            
            '''
            if sys.platform == 'win32':
                self.data_table['Check Time'].append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            else: #docker 需加8小時
                self.data_table['Check Time'].append( (datetime.datetime.now()  + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') )
            '''

            
            count += 1# 這是 每個 sport / inplay 會延展 ,下個近來 就會清空
            try:    
                match_url = inplay_url +  f"sid={sid}&iid={iid}&vd={vd}"
                r = self.session.get(url = match_url  ,  headers=self.headers ).json()
            except Exception as e:
                status_flag = 'Fail'
                error_count = error_count + 1
                fail_name = self.tournament_name[str(iid)  ][0]# list 0
                fail_tnName = self.tournament_name[str(iid)  ][1]# list 1

                Failmsg =  'inplay: %s : , fail_name: %s , fail_tnName: %s get有誤 : %s ,需確認'%(self.play_type ,     fail_name ,fail_tnName ,  e)
                self.log.error(Failmsg)
                self.data_table['Result'].append( status_flag )
                
                for key in self.data_table.keys():
                    if key == 'Reason':
                        self.data_table[key].append(Failmsg)
                    elif key in ['Inplay' , 'sport', 'iid' , 'index' , 'Check Time' , 'Result']:
                        continue

                    else:
                        self.data_table[key].append('')

                #self.send_error_msg(msg = Failmsg )
                continue
            
            
            if str(r['code'] ) != '0':
                fail_name = self.tournament_name[str(iid)  ][0]# list 0
                fail_tnName = self.tournament_name[str(iid)  ][1]# list 1

                self.data_table['tnName'].append( fail_tnName )
                self.data_table['name'].append( fail_name )

                Failmsg =  'reposense:  %s '%( r ) # 放到頁面 , 不用再放 sid /iid 相關 , 表格 看的出來
                log_msg = 'reposense:  %s , sid: %s , iid: %s , inplay: %s , fail_name: %s , fail_tnName: %s 取得 code不為 0 '%( r, sid , iid , self.play_type , fail_name , fail_tnName)
                self.log.error(log_msg )
                error_count = error_count + 1
                status_flag = 'Fail'
                self.data_table['Result'].append( status_flag )
                
                for key in self.data_table.keys():
                    if key == 'Reason':
                        self.data_table[key].append(Failmsg)
                    
                    elif key in ['Inplay' , 'sport', 'iid' ,'index' , 'Check Time' , 'Result' , 'tnName' , 'name']:
                        continue

                    else:
                        self.data_table[key].append('')

                #self.send_error_msg(msg = log_msg )  code不為0 先不寄
                continue


            #gifMid = r['data']['data']['gifMid']
            #bmid = r['data']['data']['mids']['bmid']
            #self.data_table['gifMid'].append(str(gifMid) )
            #self.data_table['bmid'].append(str(bmid) )

            kickoffDT = r['data']['data']['kickoffDT']
            self.data_table['Kickoff Time'].append(kickoffDT)

            tnName = r['data']['data']['tnName']
            self.data_table['tnName'].append(tnName)
            name = r['data']['data']['name']
            self.data_table['name'].append(name)

            gifs = '' # 先初始 , 需要拿來 判斷 gifs 是真的沒有在response 還是 有 gifs 但裡面為空
            try:
                gifs =  r['data']['data']['gifs'] # 這個 正常 會吐出 list , 取得 第一個順序的  source
                source = gifs[0]['source']

                if source in ['b' , 'c']:
                    mid =  gifs[0]['info']
                    
                    if source == 'b':
                        dr_url = f"https://en-sports-stream.{self.env}.thnors.com/?mid={mid}&type=radarPitch&sid={sid}&lang=zh"
                        catch_element = 'sr-lmt-wrap'
                    
                    else: # c 
                        dr_url = f'https://en-sports-stream.{self.env}.thnors.com/?mid={mid}&type=geniusStream&sid={sid}&lang=zh'
                        catch_element = 'bg-pager-pages-container'



                else: # source S , 直接取得url
                    dr_url = gifs[0]['info']
                    catch_element = 'msg-tip'

            except Exception as e : # 正常是 該iid 沒有 gifs 
                self.log.error('error: %s , gifs: %s'%(e, gifs)   )  
                if gifs == '': #  代表 gifs 沒有在 reponse
                    gifs = 'None'
                source = 'None'
                mid = 'None'
                dr_url = ''


            self.data_table['gifs'].append(str(gifs) )
            self.data_table['mid'].append(str(mid) )
            self.data_table['stream url'].append(str(dr_url) )
            self.data_table['source'].append(str(source) )

            self.log.info('iid : %s  , mid: %s , kickoffDT : %s , tnName: %s , name: %s , source: %s '%(iid   ,mid , kickoffDT ,tnName ,  name , source)  )

            
            pic_name = '%s_%s'%(sid  , iid )
            iframe_flag = ''
            try:
                # 新邏輯 , 不用對比 gifmid bmid , 直接從 gifs 裡面去抓 資訊
                if gifs == 'None': # 沒有gifs
                    Failmsg = ' gifs 為None '
                    self.data_table['Screenshot'].append('')
                    assert False

                elif source == 'None': # gifs 為空 ,沒資料
                    Failmsg = ' gifs 資料為空 '
                    self.data_table['Screenshot'].append('')
                    assert False
                
                

                else: # 正常行為
                    self.log.info('dr_url: %s'%dr_url )
                    try:
                        dr.get(dr_url)
                    except Exception as e:
                        Failmsg = 'get url 有誤: %s '%e
                        self.data_table['Screenshot'].append('')
                        assert False

                    
                    
                    try:
                        if source == 'c':  #  需先切換iframe 才能 做元素確認
                            WebDriverWait(dr, 40 ).until(ec.presence_of_element_located((By.ID,  
                                    'betgenius-iframe' )))
                            dr.switch_to.frame('betgenius-iframe')
                            iframe_flag = 'true'


                        # 確認視蘋
                        WebDriverWait(dr, 40 ).until(ec.presence_of_element_located((By.CLASS_NAME,  
                                    catch_element )))
                        
                        time.sleep(3)
                        self.getImage(driver = dr ,  pic_name = pic_name) # 截圖 , 會增加 Screenshot 內容

                    except:
                        Failmsg = '視頻顯示需確認'
                        self.getImage(driver = dr ,  pic_name = pic_name) # 截圖 , 會增加 Screenshot 內容
                        assert False
                    

                    # 正確走這

                    self.data_table['Result'].append('Pass')
                    self.data_table['Reason'].append('')

                '''
                原邏輯
                if gifMid != bmid:# 通常這邊是   gifMid != bmid 通常是  其中一個為0
                    Failmsg = '%s - %s - iid: %s :  gifMid: %s 不等於 bmid: %s'%(self.sport_name ,self.play_type , iid, gifMid , bmid) 
                    
                    if str(gifMid) == '0':
                        mimd = bmid
                    else:
                        mimd = gifMid
                    
                    # 這邊 gifMid != bmid 通常是  其中一個為0 , 這邊 仍需get 又值的畫面 截圖
                    dr_url = f"https://en-{vendor_id}-sports-stream.{self.env}.68a.site/?mid={mimd}&type=radarPitch&sid={sid}&lang=zh"
                    dr.get(dr_url)

                    try:
                        WebDriverWait(dr, 40 ).until(ec.presence_of_element_located((By.CLASS_NAME,  
                                'sr-lmt-wrap')))
                        #time.sleep(0.5)
                        non_game = ''
                        try:
                            WebDriverWait(dr, 10 ).until(ec.presence_of_element_located((By.CLASS_NAME,  
                                'sr-lmt-0-ms-countdown__text sr-lmt-0-ms-countdown__title srt-text-secondary srm-is-uppercasep')))# 比賽未涉及 的元素
                            non_game = 'true'
                        except:
                            pass
                        if '比赛未涉及' in dr.page_source or non_game == 'true':# 這邊算成功案例
                            status_flag = "Pass"
                            self.data_table['Result'].append(status_flag)
                            self.data_table['Reason'].append(Failmsg  + "\n"+ "比赛未涉及")
                            self.getImage(driver = dr , pic_name = pic_name)
                        else:
                            assert False# 有視頻  但是 沒有 比賽未涉及


                    except: # 沒視頻
                        self.getImage(driver = dr , pic_name = pic_name)
                        assert False
                
                
                
                else:
                    if gifMid == 0  and  bmid == 0:# 不做 get
                        self.data_table['Result'].append('None')
                        self.data_table['Reason'].append('gifMid 和 bmid 皆為 0 ')
                        self.data_table['Screenshot'].append('')
                        
                        continue
                    
                    
                    else:
                        dr_url = f"https://en-{vendor_id}-sports-stream.{self.env}.68a.site/?mid={gifMid}&type=radarPitch&sid={sid}&lang=zh"
                        self.log.info('dr_url: %s'%dr_url)
                        dr.get(dr_url)
                        try:
                            WebDriverWait(dr, 40 ).until(ec.presence_of_element_located((By.CLASS_NAME,  
                                        'sr-lmt-wrap')))
                            #self.Allure_image(browser = dr)
                            self.getImage(driver = dr ,  pic_name = pic_name)
                        except:
                            Failmsg =  '%s - %s - iid: %s ,\n url: %s 視頻顯示需確認'%(self.sport_name ,self.play_type , iid , dr_url)
                            
                            #self.odds_send_msg( sid = sid , iid = iid ,tnName = tnName , name = name , bmid = bmid ,gifMid = gifMid, run_inplay = self.play_type, kickoffTime = kickoffDT , Failmsg = Failmsg)
                            self.getImage(driver = dr ,  pic_name = pic_name)
                            assert False
                    
                    status_flag = "Pass"
                    self.data_table['Result'].append(status_flag)
                    self.data_table['Reason'].append('')
                '''
                
            
            
            
            except:
                #寄送訊息 先暫停
                #self.odds_send_msg( sid = sid , iid = iid ,tnName = tnName , name = name , run_inplay = self.play_type, kickoffTime = kickoffDT , Failmsg = Failmsg)
                self.log.error(' Failmsg : %s'%Failmsg)
                status_flag = 'Fail'
                error_count = error_count + 1

                self.data_table['Result'].append(status_flag)
                self.data_table['Reason'].append(Failmsg)

            if iframe_flag == 'true' and source == 'c': # 須把 iframe 切回 , 否則 下個視蘋  無法確認元素
                dr.switch_to.default_content()

            #這邊多檢查  data_table的  list長度是否一至 , 否則產報告會有問題
            for value in self.data_table.values():
                if len(value) != self.all_count:
                    value.append('補期長度需確認')


           
            
        try:
            dr.quit() 

            #存放 Linework的數據
            self.linework_data[self.play_type]['count'].append(count)
            self.linework_data[self.play_type]['error_count'].append(error_count)

            #存放 report的數據
            report_data_key = '%s-%s'%(self.sport_name , self.play_type)# 拿來 存放 report_data 的key
            self.report_data[report_data_key]['count'].append(count)
            self.report_data[report_data_key]['error_count'].append(error_count)

            return True

        except Exception as e:
            self.log.error('sport_match: %s'%e)
            return False

    def retrun_table_html(self ,report_data): # 失敗率的 資料結構
        tr_sring = "<tr>"
        for value in report_data.values():
            tr_sring += " <td class='tg-r27s'>%s</td>"%value 
        tr_sring += "</tr>"
        #self.log.info('tr_sring: %s'%tr_sring)
        return tr_sring


    def write_html(self ,fail_data):
        Func = open("./report/%s/report.html"%self.current_folder ,"w" ,encoding='utf-8')


        # Adding input data to the HTML file
        Func.write('''<html><head> 
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>Report</title>
        <script src="https://cdn.staticfile.org/jquery/3.2.1/jquery.min.js"></script>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.22/css/jquery.dataTables.css">
        <style type="text/css">
            .dataframe{font-size:3pt;border:2px solid #b613de; text-align: center;}
            table.dataTable tbody tr.even {
                background-color: #fff0fe ;
            }
            table.dataTable tbody tr.even:hover {
                background-color: #e9a6e4 ;
            }
            .dataframe tr:hover{background:#e8e8e8;cursor:pointer;}

            th:hover{

                color : #6f008b
            }
            th.sorting, th.sorting_asc, th.sorting_desc {
                text-align: center;
                color: #eda3ff
            }
            table.tg {
                margin: 0 auto;
            }
            th {
                text-align: center;
                color: #492152
            }
            .sport_data {
                margin-left: 10px;
            }
            .sport_key {
                color: #9200ab;
                font-size: medium;
                font-style: italic;
                font-family: fangsong;
                font-weight: 600;
                display: inline-block;
            }
            .sport_value {
                color: #ff9800;
                font-size: unset;
                display: unset;
                margin: 10px;
                font-style: oblique;
            }
            .tg  {border-collapse:collapse;border-spacing:0;}
            .tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
            overflow:hidden;padding:9px 15px;word-break:normal;}
            .tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
            font-weight:normal;overflow:hidden;padding:9px 15px;word-break:normal;}
            .tg .tg-ycto{background-color:#eadef7;border-color:#8b0987;color:#9710f6;font-family:"Lucida Console", Monaco, monospace !important;
            font-size:20px;font-weight:bold;text-align:center;vertical-align:middle}
            .tg .tg-qq58{background-color:#fff6d9;border-color:#8b0987;color:#ec9d00;font-family:"Lucida Console", Monaco, monospace !important;
            font-size:14px;font-style:italic;text-align:center;vertical-align:top}
            .tg .tg-gmpv{background-color:#eeeaf2;border-color:#8b0987;color:#9317ba;font-family:"Lucida Console", Monaco, monospace !important;
            font-size:14px;font-weight:bold;text-align:center;vertical-align:top}
            .tg .tg-r27s{background-color:#fff6d9;border-color:inherit;text-align:center;vertical-align:top}


        </style>
        <script src="https://cdn.datatables.net/1.10.22/js/jquery.dataTables.min.js" type="text/javascript"></script>

        <script type="text/javascript">
            $(document).ready(function () {

                var type_data = []
                var data = %s
                '''%(self.data_table) +
                '''    
                var key_name = Object.keys(data)
                console.log(key_name)
                var len_data = data[key_name[0]].length//動態取得 data 第一個key 名稱的長度
                console.log(len_data)
                var tabel_text = "<table border='1' class='dataframe'><thead><tr style='text-align: right;'>"
                var nowrap_array = ['tnName' , 'name', 'Check Time' , 'Kickoff Time'] // 拿來不換行 的 array

                for (i=0;i<len_data;i++){// 動態把 key取出後, loop增加 th 方式
                    var a = []
                    $.each( key_name, function( key, value ) { // jey 為索引, value 為 data的key名稱

                        
                        if (i==0){ 
                            if ( $.inArray(  value , nowrap_array  ) > -1 ) { // 不換行
                                var newTh = "<th  style='white-space: nowrap;' >"+ value +"</th>"; 
                            }
                            else{
                                var newTh = "<th>"+ value +"</th>"; 
                            }

                        
                            tabel_text = tabel_text + newTh

                        }
                        if (data[value][i].indexOf('.png') > 1){
                            data_ = "<a href=" + data[value][i] +" target='_blank' ><img src=" + data[value][i] + " width='160px' height='80px' ></a>"
                        }
                        else{
                            data_  = data[value][i]
                            if (data_ == 'Pass'){
                                data_ = "<span style='color: #00b107;font-size: large;'>" + data_  + "</span>"
                            }
                            else if  (data_ == 'Fail'){
                                data_ = "<span style='color: #f44336;font-size: large;'>" + data_  + "</span>"
                            }
                            else{// 不換行 
                                //data_ = "<span style='white-space:nowrap;'>" + data_  + "</span>"
                                data_ =  data_ 
                            }
                        
                        }

                        a.push(data_)
                        
                    });
                    
                    type_data.push(a)// 陣列包陣列 ex: [[123],[456]]

                }
                tabel_text = tabel_text + "</tr></thead><tbody><tr><th></th></tr></tbody></table>"
                $('#data').after(tabel_text)
                $('.dataframe').DataTable( {
                    data:  type_data ,
                    "iDisplayLength": 100,
                    //dom:'lBrtip',
                    "bAutoWidth" : true,
                    "searching": true, 
                    "paging": true,
                   "lengthMenu": [30 , 50, 100 ] ,
                    "info":true,
                    "language": {
                        "search": "搜尋:",
                        "paginate": {
                            "first": "第一頁",
                            "previous": "上一頁",
                            "next": "下一頁",
                            "last": "最後一頁"
                        },
                        "info": "顯示第 _START_ 至 _END_ 項結果，共 _TOTAL_ 項",
                        "lengthMenu": "顯示 _MENU_ 項結果",
                    }
                });
                //$('.dataframe.dataTable.no-footer').css('width','120%')
                $('.dataTables_filter input').css('color','black')
                $('.dataTables_filter').css('color','black')


            })

        </script>
        </head> 
        <body>'''+
        '''
        <div style="font-size :x-large;
            text-align :center;
            margin :inherit;
            font-weight: bold;
            color: rgb(153 96 255);">動態圖自動化</div>
        <table class="tg">
            <thead>
                <tr>
                    <th class="tg-ycto" colspan="12">失敗率</th>
                </tr>
            </thead>
            <tbody>
            <tr>
                <td class="tg-qq58" colspan="4">滾球  </td>
                <td class="tg-qq58" colspan="4">今日 </td>
                <td class="tg-qq58" colspan="4">早盤  </td>
            </tr>
            <tr>
                <td class="tg-gmpv">足</td>
                <td class="tg-gmpv">籃</td>
                <td class="tg-gmpv">網</td>
                <td class="tg-gmpv">棒</td>
                <td class="tg-gmpv">足</td>
                <td class="tg-gmpv">籃</td>
                <td class="tg-gmpv">網</td>
                <td class="tg-gmpv">棒</td>
                <td class="tg-gmpv">足</td>
                <td class="tg-gmpv">籃</td>
                <td class="tg-gmpv">網</td>
                <td class="tg-gmpv">棒</td>
            </tr>
            {0}'''.format(fail_data) +
            '''
            </tbody>
            </table>
        <div id="data" style="color: #bbbbbb; display: list-item;"></div>
        </body></html>''' )

        # Saving the data into the HTML file
        Func.close()


config = configparser.ConfigParser()
config.read('config.ini', encoding="utf-8")

print(sys.argv)
if len(sys.argv) >= 2:# 傳入 env 

    env = sys.argv[1]
    config.set("config","env", str(env))
    
    sport_item = sys.argv[2]
    config.set("config","sport_item", str(sport_item) )

    inplay_list = sys.argv[3]
    config.set("config","inplay_list", str(inplay_list) )
    
    file = open("config.ini", 'w' , encoding='utf-8')
    config.write(file) 
    file.close()
else:
    pass# 不複寫config 

sport_stream = Sport_Stream()

dr =  Driver().return_driver(index = 0)# local 端 建立driver 版本 環境 ,docker 進去會直接return 
 
inplay_list = sport_stream.inplay_list     #[True , 'early' ,'today']  

sid_list = sport_stream.sport_list  #sport_stream.sport_item.keys() # sid list
print('sid_list: %s , inplay_list : %s'%(sid_list , inplay_list))

sport_stream.delete_images()#山除非今天生成的 image圖檔 (只有local)

print('start: %s - %s'%(sport_stream.env , sport_stream.site )  )
for sid in sid_list:
    
    for inplay_ in inplay_list:

        tournaments_status = sport_stream.sport_tournaments(sid = sid , inplay = inplay_ )

        if tournaments_status is  True: # 會是 false , tournament_detail 資料是空, 可能沒有賽事
            sport_stream.sport_match(sid = sid )
        else:
            pass


#print (sport_stream.data_table)
report_data = sport_stream.return_report_data()# 將資料回傳給 html
fail_data = sport_stream.retrun_table_html(report_data = report_data)# 統整失敗率的結果
sport_stream.write_html(fail_data = fail_data)

sftp_result = sport_stream.sftp_()#上傳report檔案
if sftp_result is False:
    sport_stream.send_error_msg( msg = 'sftp 上傳錯誤')#最後報告總結
    pass
else:
    pass
    sport_stream.send_summery_msg()#最後報告總結
    