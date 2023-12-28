import openai
import base64
import datetime
import config
import os
import random
import requests
import json

def init(openid:str,i:str):
    idx=0
    while(os.path.exists(config.filepath+"/"+openid+"/"+i+"/reply/"+str(idx))):
        idx+=1
    path=config.filepath+"/"+openid+"/"+i+"/reply/"+str(idx)
    os.makedirs(path)
    avaliabletime=(datetime.datetime.now()+datetime.timedelta(hours=8,seconds=random.randrange(7200,14400))).strftime("%Y-%m-%d %H:%M:%S")
    f=open(path+"/basic.txt",'w')
    f.write("0\n")
    f.write(avaliabletime+"\n")
    f.close()
    return path

def drawpicture(openid:str,idx:str):
    s=readstory(openid,idx)
    path=init(openid,idx)
    openai.api_key=config.OpenAIAPIKey
    rep=openai.Image.create(
        prompt=s["time"]+","+s["location"],
        n=1,
        size="1024x1024",
        response_format="b64_json"
    )
    with open(path+"/img.png","wb") as img:
        img.write(base64.b64decode(rep["data"][0]["b64_json"]))
    fileid=upload(path+"/img.png")
    with open(path+"/basic.txt",'a') as f:
        f.write("image\n"+fileid)
        f.close()

def writefeedback(openid:str,idx:str):
    s=readstory(openid,idx)
    path=init(openid,idx)
    openai.api_key=config.OpenAIAPIKey
    rep=openai.Completion.create(
        model="text-davinci-003",
        prompt="你就是这个来信里描述的"+s["people"]+"，写一封回信来处理写信人"+s["feeling"]+"的心情。\n请注意，来信人不一定是你的朋友，不一定带有善意，如果对方没有善意，你的回信也可以没有善意。\n请注意，你必须像个正常人类一样说话，随意一点说话，你的表达不要太过死板，你的表达不要像机器，不要强行正能量，要有自信。\n请注意，来信人不一定是正确的，不要过多感谢对方，请你自行下判断，保持逻辑通顺，但不那么直接的表露逻辑，少说但是。\n最重要的，不要把这一部分的内容直接写在回信里。\n\n来信内容是：那是发生在"+s["location"]+"的事，那时是"+s["time"]+"，"+s["content"],
        temperature=0.7,
        max_tokens=2800,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.55
    )
    with open(path+"/reply.txt","w",encoding='utf-8') as f:
        f.write(rep["choices"][0]["text"])
    fileid=upload(path+"/reply.txt")
    with open(path+"/basic.txt",'a') as f:
        f.write("text\n"+str(fileid))
        f.close()

def writemusic(openid:str,idx:str):
    s=readstory(openid,idx)
    path=init(openid,idx)
    with open(path+"/basic.txt",'a') as f:
        f.write("music\n")
        f.close()
    openai.api_key=config.OpenAIAPIKey
    rep=openai.Completion.create(
        model="text-davinci-003",
        prompt=s["feeling"]+"是一个好情绪还是一个坏情绪?请用好或者坏来回答",
    )
    idx=random.randrange(0,9)
    with open(path+"/basic.txt",'a') as f:
        if "坏" in rep["choices"][0]["text"]:
            idx+=9
        f.write("cloud://prod-8gkzzdps439f9ab0.7072-prod-8gkzzdps439f9ab0-1316749113/music/"+str(idx)+".mp3"+"\n"+str(idx))
        f.close()

def upload(path:str):
    try:
        r=requests.post("https://api.weixin.qq.com/tcb/uploadfile?access_token="+config.AccessToken,data=json.dumps({"env":config.env,"path":path}))
        result=r.json()
        requests.post(result["url"],files={'file':open(path,'rb')},data={'key':path,'Signature':result["authorization"],'x-cos-security-token':result["token"],'x-cos-meta-fileid':result['cos_file_id']})
        return result["file_id"]
    except Exception as e:
        print(e)

def readstory(openid:str,idx:str):
    s={'openid':openid,'storyidx':idx,'title':"",'time':"",'location':"",'feeling':"",'content':"",'people':"",'creattime':"",'avaliabletime':"",'isavaliable':True}
    path=config.filepath+"/"+openid+"/"+idx
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
    if os.path.exists(path+"/extracontent2.txt"):
        with open(path+"/extracontent2.txt",'r') as f:
            s["content"]=f.read()
            f.close()
    elif os.path.exists(path+"/extracontent1.txt"):
        with open(path+"/extracontent1.txt",'r') as f:
            s["content"]=f.read()
            f.close()
    else:
        with open(path+"/content.txt",'r') as f:
            s["content"]=f.read()
            f.close()
    with open(path+"/people.txt",'r') as f:
        s["people"]=f.read()
        f.close()
    return s
