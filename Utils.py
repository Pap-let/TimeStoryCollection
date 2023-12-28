import requests
from requests import ConnectTimeout
import config
import os
from config import filepath
import datetime
import threading
import Ai
import random
import time
import json
import shutil
def getAccessToken():
    while(True):
        try:
            r=requests.get("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid="+config.AppID+"&secret="+config.AppSecret,timeout=20)
            result=r.json()
            if 'errcode' in result:
                print(result)
            else:
                config.AccessToken=result['access_token']
                print("AccessToken:"+result['access_token'])
        except(ConnectTimeout):
            print("Error:Timeout while getting AccessToken")
        time.sleep(7000)

def writedata(openid:str,title:str,time:str,location:str,feeling:str,content:str,people:str):
    idx=0
    while(os.path.exists(filepath+"/"+openid+"/"+str(idx))):
        idx+=1
    path=filepath+"/"+openid+"/"+str(idx)
    os.makedirs(path)
    os.makedirs(path+"/reply")
    with open(path+"/basic.txt",'a') as file:
        creattime=(datetime.datetime.now()+datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        file.write(title+"\n"+time+"\n"+creattime)
        file.close()
    with open(path+"/location.txt",'a') as file:
        file.write(location)
        file.close()
    with open(path+"/feeling.txt",'a') as file:
        file.write(feeling)
        file.close()
    with open(path+"/content.txt",'a') as file:
        file.write(content)
        file.close()
    with open(path+"/people.txt",'a') as file:
        file.write(people)
        file.close()
    ti=threading.Thread(target=Ai.drawpicture,args=(openid,str(idx)))
    ti.start()
    tt=threading.Thread(target=Ai.writefeedback,args=(openid,str(idx)))
    tt.start()

def extrareply(openid:str,idx:str,content:str):
    path=filepath+"/"+openid+"/"+idx
    if os.path.exists(path+"/extracontent1.txt"):
        with open(path+"/extracontent2.txt",'w') as f:
            f.write(content)
    else:
        with open(path+"/extracontent1.txt",'w') as f:
            f.write(content)
    t=threading.Thread(target=random.choice([Ai.drawpicture,Ai.writefeedback,Ai.writemusic]),args=(openid,str(idx)))
    t.start()

def readstorys(openid:str):
    storys=[]
    path=filepath+"/"+openid+"/"
    filelist=os.listdir(path)
    for idx in filelist:
        s=readstory(openid,idx)
        storys.append(s)
    return storys

def readstory(openid:str,idx:str):
    s={'openid':openid,'storyidx':idx,'title':"",'time':"",'location':"",'feeling':"",'content':"",'people':"",'creattime':""}
    path=filepath+"/"+openid+"/"+idx
    with open(path+"/basic.txt") as f:
        s["title"]=f.readline().strip()
        s["time"]=f.readline().strip()
        s["creattime"]=f.readline().strip()
        f.close()
    with open(path+"/location.txt",'r') as f:
        s["location"]=f.read()
        f.close()
    with open(path+"/feeling.txt",'r') as f:
        s["feeling"]=f.read()
        f.close()
    with open(path+"/content.txt",'r') as f:
        s["content"]=f.read()
        f.close()
    with open(path+"/people.txt",'r') as f:
        s["people"]=f.read()
        f.close()
    if os.path.exists(path+"/extracontent1.txt"):
        with open(path+"/extracontent1.txt",'r') as f:
            s["extracontent1"]=f.read()
            f.close()
    if os.path.exists(path+"/extracontent2.txt"):
        with open(path+"/extracontent2.txt",'r') as f:
            s["extracontent2"]=f.read()
            f.close()
    return s

def readreplys(openid:str):
    replys=[]
    path=filepath+"/"+openid+"/"
    filelist=os.listdir(path)
    for idx in filelist:
        replys=replys+readreply(openid,idx)
    return replys

def readreply(openid:str,idx:str):
    path=filepath+"/"+openid+"/"+idx+"/reply"
    reply=[]
    for i in os.listdir(path):
        r={'openid':openid,'storyidx':idx,"replyidx":i,'haveread':True,'replytype':"",'avaliabletime':"",'isavaliable':True}
        with open(path+"/"+i+"/basic.txt") as f:
            if(f.readline().strip()=="0"):
                r["haveread"]=False
            r["avaliabletime"]=f.readline().strip()
            r["replytype"]=f.readline().strip()
            r["replyurl"]=f.readline().strip()
            if r["replytype"]=="music":
                r["musicdata"]=f.readline().strip()
                with open("./music/"+r["musicdata"]+".txt") as g:
                    r["musicdata"]=g.read()
                    g.close()
            else:
                if len(os.listdir(path+"/"+i))==1:
                    continue
            f.close()
        if r["replytype"]=="text":
            with open(path+"/"+i+"/reply.txt") as f:
                r["replyurl"]=f.read()
                f.close()
        if(datetime.datetime.strptime(r["avaliabletime"],"%Y-%m-%d %H:%M:%S")>(datetime.datetime.now()+datetime.timedelta(hours=8))):
            r["isavaliable"]=False
        reply.append(r)
    return reply

def getdownloadlink(fileid:str):
    try:
        r=requests.post(url="https://api.weixin.qq.com/tcb/batchdownloadfile?access_token="+config.AccessToken,data=json.dumps({"env":config.env,"file_list":[{"fileid":fileid,"max_age":7200}]}))
        result=r.json()
        if(result["errcode"]!=0):
            print(result["errmsg"])
            return "Error"
        else:
            return result["file_list"][0]["download_url"]
    except Exception as e:
        print(e)
        return "Error"

def setreplymine(myopenid:str,openid:str,storyidx:str,replyidx:str):
    idx=0
    while(os.path.exists(filepath+"/"+myopenid+"/a/reply/"+str(idx))):
        idx+=1
    path=filepath+"/"+myopenid+"/a/reply/"+str(idx)
    os.makedirs(path)
    for i in os.listdir(filepath+"/"+openid+"/"+storyidx+"/reply/"+replyidx):
        shutil.copy(filepath+"/"+openid+"/"+storyidx+"/reply/"+replyidx+"/"+i, path)