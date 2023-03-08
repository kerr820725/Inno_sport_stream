class Env:
    def __init__(self):   
        self.env_dict = {
            '長城':  {'stg': {'platform_URL': 'https://en-vd001-tiger-portal.innostg.site' , 'platform_api_URL': 'https://tiger-api.innostg.site/product'} , 
            'uat': {'platform_URL': 'https://en-vd001-tiger-portal.innouat.site' , 'platform_api_URL': 'https://vd001-tiger-api.innouat.site/product'}
                , 'prod':  {'platform_URL': 'https://www.978bet1.com'  , 'platform_api_URL': 'https://vd001-tiger-api.nfttang.com/platform' }  ,  'vendor_id': 'vd001' ,
                'lan':   'id-id'
                
            } ,
            '谷歌':  {'stg':  {'platform_URL': 'https://en-vd002-tiger-portal.innostg.site'  , 'platform_api_URL': 'https://tiger-api.innostg.site/product' ,
                "sport_api_URL": "https://tiger-api.innostg.site/product"} ,
                'uat': {'platform_URL': 'https://en-vd002-tiger-portal.innouat.site' , 'platform_api_URL': 'https://vd002-tiger-api.innouat.site/product',
                "sport_api_URL": "https://sports-api.innouat.site/product"  } 
            , 'prod':  {'platform_URL': 'https://9393e4.com'   , 'platform_api_URL': 'https://vd002-tiger-api.czgecko.com/product' }  ,  'vendor_id': 'vd002' ,
                'lan':   'zh-cn' 
            } ,

            '新六':  {'stg':  {'platform_URL': 'https://en-vd003-tiger-portal.innostg.site', 'platform_api_URL': 'https://tiger-api.innostg.site/product' } , 
            'uat': {'platform_URL': 'https://en-vd003-tiger-portal.innouat.site' , 'platform_api_URL': 'https://vd003-tiger-api.innouat.site/product'}
            , 'prod':  {'platform_URL': 'https://en-vd003-tiger-portal.mppwr.com' , 'platform_api_URL': 'https://vd003-tiger-api.weicunwu.com/platform'   }    ,'vendor_id': 'vd003' ,
                'lan':   'zh-cn'  
            } ,

            '瑞銀':  {'stg':  {'platform_URL': 'https://en-vd004-tiger-portal.innostg.site' , 'platform_api_URL': 'https://tiger-api.innostg.site/product'} , 
            'uat':{'platform_URL': 'https://en-vd004-tiger-portal.innouat.site' , 'platform_api_URL': 'https://vd004-tiger-api.innouat.site/product'}
            , 'prod': {'platform_URL': 'https://6686g10.com'  , 'platform_api_URL': 'https://vd004-tiger-api.80wa.com/product' }   ,'vendor_id': 'vd004' ,
              'lan':   'en-us'   
            } ,
        
        } 
        self.sport_item =  {
            "1" : "足球",
            "2" : "籃球",
            "3" : "網球",
            "4" : "棒球" }

    


