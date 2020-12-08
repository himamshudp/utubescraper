#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import numpy as np
import time
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from selenium.webdriver.chrome.options import Options
import warnings
warnings.filterwarnings('ignore')


# In[4]:


def y_scrap():
    
    url = "https://www.youtube.com/c/rajshrifood/videos"    
    
     # headless chorme
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    #forlocal machine
    chromedriver = 'E://chromedriver.exe'
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chrome_options)
    
    #for cloud
    #chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    #driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    
    ######### To scroll bar automatically til end of page of you tube channel page #########
    driver.get(url)
    old_position = 0
    new_position = None

    while new_position != old_position:
        # Get old scroll position
        old_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))
        # Sleep and Scroll
        time.sleep(7)
        driver.execute_script((
                "var scrollingElement = (document.scrollingElement ||"
                " document.body);scrollingElement.scrollTop ="
                " scrollingElement.scrollHeight;"))
        # Get new position
        new_position = driver.execute_script(
                ("return (window.pageYOffset !== undefined) ?"
                 " window.pageYOffset : (document.documentElement ||"
                 " document.body.parentNode || document.body);"))
    
    #################################### Scrapping urls ##################################### 
    
    datas = driver.find_elements_by_css_selector("ytd-grid-video-renderer")
    links = [] ###### Creating a empty list to save all fetched urls
    
    for data in datas:
        try:
            link = data.find_element_by_css_selector("#video-title").get_attribute("href")
            links.append(link)               
        except:
            links.append("")
    link = links
    url = link[:2]
    print(len(links))
    
    
    alldetails=[] ###### Creating a empty list to save all fetched data
    
    for i in url:
        driver.get(i)
        wait = WebDriverWait(driver, 10)
        time.sleep(7)
        #driver.find_element_by_xpath('/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[4]/div[1]/div/div[6]/div[3]/ytd-video-secondary-info-renderer/div/ytd-expander/paper-button[2]/yt-formatted-string').click()
        print(i )
        ##### Scrapping description_of_video 
        try:
            description_of_video=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"div#description yt-formatted-string"))).text    
        except:
            description_of_video=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#description > yt-formatted-string"))).text
       
        ##### Scrapping title,likes,views,upload date of videos
        title_of_video=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"h1.title yt-formatted-string"))).text
        video_likes=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"ytd-toggle-button-renderer.style-scope:nth-child(1) > a:nth-child(1) > yt-formatted-string:nth-child(2)"))).text
        views_of_video=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,".view-count"))).text
        upload_date =wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#date>yt-formatted-string"))).text

        temlj={'Link':i,
               'Title':title_of_video,
               'Likes':video_likes,
               'Views':views_of_video,
               'Description':description_of_video,
               'Upload_Date':upload_date
              }
        alldetails.append(temlj)
    
    df=pd.DataFrame(alldetails)  ######### To save all scrap data in main dataframe i.e. df 
    
    driver.close()
    
    ######################### Scrapping process till here will complete #######################################
    
    ###########################################################################################################
    #                            Data Cleaning and column creation
    ###########################################################################################################
    
    ############ lowering the dataset to maintaing uniformity in data
    df[['Description','Title']] = df[['Description','Title']].apply(lambda x: x.astype(str).str.lower())
    
    ############ Removing all special characters
    df=df.replace({'\n|\\n':'# '}, regex=True)
    df[['Description','Title']] = df[['Description','Title']].replace({r'[^A-Za-z0-9]':' ',r'[\s]+':' '},regex=True)
    df["Likes"]=df["Likes"].replace({r'nan':'0'},regex=True)
    df['Likes'] = df['Likes'].replace({'K|k': '*1e3','M|m': '*1e6'}, regex=True).map(pd.eval).astype(int)
    df["Views"]=df["Views"].replace({r'[^0-9]':''},regex=True)
    
    # Drop the rows containing specific word/symbol to remove unwanted links
    df = df[~df['Title'].str.contains('contest|youtube|you tube|live from|live with|live part|our first|tips for kitchen|tricks for kitchen|challenge|trailer|how to clean|how to store|how to preserve|how to use|subscriber|how to cut|launch|promotion|website|kitchen tips|kitchen tricks|thank|question|studio|vote|announce|www')]
    
    ########## Reading the standard Ingredient list to create columns like 
    df_col=pd.read_excel("Standard_list_ingredients_process_spices_02_10_20.xlsx")
    
    df_col=df_col.apply(lambda x: x.astype(str).str.lower()) ##### Converting all columns data to lower
    ##### Creating column into list
    std_ingred_list=df_col["Ingredients"].tolist()
    description=df["Description"].tolist()
    spice_list=df_col["Spices"].tolist()
    spice_list = [x for x in spice_list if str(x) != 'nan'] # removed nan value from spicelist
    
    try:
        df_ingredients=df['ingredients_data']=df['Description'].str.split('Ingredients').str[0]
    except:
        df_ingredients=df['ingredients_data']=df['Description'].str.split('Ingredients').str[1]

    df_ingredients=df['ingredients_data']=df['ingredients_data'].str.split('kitchen').str[0]
    ingredients_data=df['ingredients_data']=df['ingredients_data'].tolist()
    
    ############# Replacing all hindi and wrong spelling ingredients with correct one
    replacement_pname = {'aam ':'mango', 'badam':'almond', 'aloo|aalu|batata':'potato','amchur|dry mango|dry mango powder':'amchoor',
                       'anardana':'pomegranate', 'anjeer':'anjir', 'babycorn':'baby corn','baingan':'brinjal', 'bay leaf|bay leave':'tej patta',
                        'beet root ':'beetroot','lady fingure|okra':'bhindi', 'cabagge ':'cabbage', 'caromseed|carrom seeds|ajjwain':'carom seed',
                       'gobi|gobhi':'cauliflower', 'cashewnut,kaju':'cashew', 'cheese cube|cheese ram,':'cheese', 'cherrie':'cherry',
                        'chilli|chilly|chillies|chilies':'chili', 'choco chips':'chocolate  chips','chola|futana':'chole', 'cinnamon|dalchini':'cinammon',
                        'coriander leave':'coriander stem', 'cornflakes':'corn flakes', 'cummin':'cumin','dahi|yogurt':'curd','dalia':'daliya',
                        'methi':'fenugreek','frenchbeans':'french beans', 'ggpaste|gg paste|ginger garlic paste':'garlicgingerpaste',
                        'gulabjal|gulab jal':'rose water', 'icecream':'ice cream', 'kashmiri red chili':'kashmiri red chilli', 'icecream':'ice cream',
                        'khuskhus|khus khus':'poppy seed', 'maggi magic masala':'maggi masala', 'pudina|mint leaves':'mint', 'rai':'mustard',
                        'pyaaz|pyaz':'onion','pav|ladi paav|ladi pav':'paav', 'panchphoron':'panch phoron' , 'pohe|rice flacks':'poha', 'poppyseeds':'poppy seeds',
                       'rollsheet':'roll sheet', 'sambhar masala':'sambar masala', 'samosapatti':'samosa patti', 'semolina|suji':'rawa',
                       'shahijira|black cumin':'shahi cummin', 'shakkar':'sugar', 'sichuan peppercorns':'sichuan pepper corns' , 'soy sauce':'soya sauce',
                        'strawberries':'strawberry', 'sweetcorn':'sweet corn', 'triphal|teppal':'trifala', 'whitepepper':'white pepper',
                       'chawli':'cowpea', 'moth bean':'mataki' , 'tur|toor dal|arhar dal|tuvar dal':'tur dal', 'onion seeds':'kalonji',
                       'badishep|saunf':'fennal', 'gram|bengal gram':'besan', 'ajinomoto':'msg', 'chawal':'rice', 'baingan':'cowpea', 
                        'eating soda':'baking soda', 'laung':'clove', 'til':'sesame', 'drinking soda':'club soda', 'sitaphal':'custard apple',
                        'soya grannule|soyabean':'soya chunks', 'staranis|star anis':'anis', 'asafoetida|hing':'heeng', 'barista':'birista',
                        'dhaniya':'coriender', 'alam|fitkari':'alum', 'charcoal':'coal', 'vatana|matar':'peas', 'spinach':'palak',
                        'lemon juice':'citric acid', 'gajar':'carrot', 'ketchup':'tomato sauce', 'lime':'lemon', 'malai':'cream','maka':'maize',
                        'masoor dal':'masur dal', 'plain flour':'maida', 'button mushroom':'mushroom' }
    
    df['ingredients_data'] = (df['ingredients_data'].astype("str")
                              .str.rstrip()   ## is used to remove extra white space
                              .replace(replacement_pname, regex=True)) ### used to find pattern n replace
    
    ####### Extracting Ingredient list from Description
    
    all_ingred=[] ###### Creating a empty list to append all ingredients
    for j in range(len(ingredients_data)):
        list1=[]
        for i in range(len(std_ingred_list)):
            try:
                    if std_ingred_list[i] in ingredients_data[j]:
                        list1.append(std_ingred_list[i])
            except:
                        list1=[]
        all_ingred.append(list1)
        
    df['ingredients']=all_ingred ##### Saving ingredients list in data frame column  
    
    ########## To count no. of ingrdients used in recipes
    ingredientcount=[]
    for i in range(len(all_ingred)):
        count=len(all_ingred[i])
        ingredientcount.append(count)

    df['ingredientcount']=ingredientcount ##### Saving ingredient count list in data frame column 
    
    ######## To create list of spices used in recipes using static list of spices
    ######## compairing standard list  with Description and appending the spice match values
    
    all_spices=[]
    for j in range(len(ingredients_data)):
        list2=[]
        for i in range(len(spice_list)):
            try:
                    if spice_list[i] in ingredients_data[j]:
                        list2.append(spice_list[i])
            except:
                        list2=[]
        all_spices.append(list2)
        
    df['Spices']=all_spices ##### Saving spice list in data frame column 
        
    ########### To count no. of spices used in recipes
    
    spicescount=[]
    for i in range(len(all_spices)):
        count=len(all_spices[i])
        spicescount.append(count)

    df['spicescount']=spicescount  ##### Saving spice count list in data frame column  

    ########## Input dataset column creation
    
    col_name_desc=df_col["Agescore Description"].tolist() ##### Creating column into list
    col_name_title=df_col["Agescore Title"].tolist()      ##### Creating column into list
    
    for col in col_name_desc:
        try:
            df[col] = pd.np.where(df['ingredients_data'].str.contains(col),1,0)
        except:
            pass

    for col1 in col_name_title:
        try:
            df[col1] =pd.np.where(df['Title'].str.contains(col1),1,0)
        except:
            pass
    
    ######### Cleaning Upload_Date column
    df["Upload_Date"]=df["Upload_Date"].replace({r'Premiered ':'',r'Streamed live on ':''},regex=True)
    
    ######## To convert all scrapped dates in same date format
    upload_date=df["Upload_Date"].tolist() ##### Creating column into list
    dates = []
    for i in (upload_date):
        dates.append(pd.to_datetime(i))
    
    df['Upload_Date']=pd.DataFrame(dates)  ##### Saving dates list in data frame column  
    
    ######### Final main dataframe
    print(df)
    
    ###################################------------------###############################
    """  
    #firebase
    firebase_app = None
    PROJECT_ID = 'webdatascaper'

    IS_EXTERNAL_PLATFORM = True # False if using Cloud Functions

    #if firebase_app:
    #    return firebase_app

    import firebase_admin
    from firebase_admin import credentials

    if IS_EXTERNAL_PLATFORM:
        cred = credentials.Certificate('webdatascaper-firebase-adminsdk-r9721-6539dd32b9.json')
    else:
        cred = credentials.ApplicationDefault()

    firebase_app = firebase_admin.initialize_app(cred, {'storageBucket': f"{PROJECT_ID}.appspot.com"})

    name = '/Dmart/dmart_30nov.json'
    bucket = storage.bucket()
    blob = bucket.blob(name)
    blob.upload_from_string(json.dumps(data, indent=2))
    data=json.loads(blob.download_as_string())
    print("file Uploaded")
    
    """


# In[ ]:



y_scrap()


# In[ ]:




