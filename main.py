import os
import shutil
import config
from config import filepath
import json
import requests
from requests import ConnectTimeout
from flask import Flask,request,jsonify
from flask_cors import CORS
import threading,inspect,ctypes
from Utils import setreplymine,writedata,readstorys,readstory,readreplys,readreply,extrareply,getAccessToken,getdownloadlink

app=Flask(__name__)
CORS(app,resources={r'/*':{"origins":"*"}})

if(not(os.path.exists(filepath))):
    os.makedirs(filepath)
open(filepath+"/globalstory.txt",'w')

def _async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

@app.route('/login',methods=['GET'])
def login():
    if request.method=="GET":
        jsondata={"openid":"","code":200,"msg":"ok"}
        js_code=request.args.get('code')
        try:
            r=requests.get("https://api.weixin.qq.com/sns/jscode2session?appid="+config.AppID+"&secret="+config.AppSecret+"&js_code="+js_code+"&grant_type=authorization_code",timeout=20)
            result=r.json()
            if 'errcode' in result:
                print(result['errmsg'])
                jsondata["code"]=result['errcode']
                jsondata["msg"]=result['errmsg']
            else:
                if(not(os.path.exists(filepath+"/"+result['openid']))):
                    os.makedirs(filepath+"/"+result['openid']+"/a/reply")
                    path=filepath+"/"+result['openid']+"/a"
                    f=open(path+"/basic.txt",'a')
                    f.write("回声\n")
                    f.close()
                    open(path+"/location.txt",'a')
                    open(path+"/feeling.txt",'a')
                    open(path+"/content.txt",'a')
                    open(path+"/people.txt",'a')
                    open(path+"/extracontent1.txt",'a')
                    open(path+"/extracontent2.txt",'a')
                jsondata["openid"]=result['openid']
        except(ConnectTimeout):
            print("Error:Timeout while connecting to WeChat Server")
            jsondata["code"]=404
            jsondata["msg"]="Timeout while connecting to WeChat Server"
        except Exception as e:
            print(e)
            jsondata["code"]=500
            jsondata["msg"]="Internal Error"
        return jsonify(jsondata)
        
@app.route('/newstory',methods=['POST'])
def newstory():
    if request.method=="POST":
        jsondata={"code":200,"msg":"ok"}
        result=json.loads(request.get_data(as_text=True))
        '''database=pymysql.connect(host=DBHost,user=DBUser,password=DBPassword,database=DB)
        cursor=database.cursor()
        cursor.execute("select openid from user where openid=\""+str(result['openid'])+"\"")
        data=cursor.fetchone()'''
        if not(os.path.exists(filepath+"/"+result['openid'])):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            writedata(str(result['openid']),str(result['title']),str(result['time']),str(result['location']),str(result['feeling']),str(result['content']),str(result['people']))
        return jsonify(jsondata)

@app.route('/newreply',methods=['POST'])
def newreply():
    if request.method=="POST":
        jsondata={"code":200,"msg":"ok"}
        result=json.loads(request.get_data(as_text=True))
        openid=result['openid']
        idx=str(result['storyidx'])
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+idx)):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                if os.path.exists(filepath+"/"+openid+"/"+idx+"/extracontent2.txt"):
                    jsondata["code"]=-5
                    jsondata["msg"]="Reach the max extrareply"
                else:
                    extrareply(openid,idx,result['content'])
        return jsonify(jsondata)

@app.route('/getlist',methods=['GET'])
def getlist():
    if request.method=="GET":
        jsondata={"code":200,"msg":"ok","storylist":[],"replylist":[]}
        openid=request.args.get('openid')
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            sls=[]
            s=readstorys(openid)
            for i in s:
                sls.append({"title":i["title"],"creattime":i["creattime"],"storyidx":i["storyidx"]})
            jsondata["storylist"]=sls
            rls=[]
            r=readreplys(openid)
            for i in r:
                rls.append({"replytype":i["replytype"],"haveread":i["haveread"],"avaliabletime":i["avaliabletime"],"isavaliable":i["isavaliable"],"replyidx":i["replyidx"],"storyidx":i["storyidx"]})
            jsondata["replylist"]=rls
        return jsonify(jsondata)

@app.route('/getstory',methods=['GET'])
def getstory():
    if request.method=="GET":
        jsondata={"code":200,"msg":"ok","story":[]}
        openid=request.args.get('openid')
        idx=request.args.get('storyidx')
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+str(idx))):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                jsondata["story"]=readstory(openid,idx)
        return jsonify(jsondata)

@app.route('/getreply',methods=['GET'])
def getreply():
    if request.method=="GET":
        jsondata={"code":-3,"msg":"No requested replyidx"}
        openid=request.args.get('openid')
        sidx=request.args.get('storyidx')
        ridx=request.args.get('replyidx')
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+str(sidx))):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                r=readreply(openid,sidx)
                for i in r:
                    if i["replyidx"]==str(ridx):
                        if(not(i["isavaliable"])):
                            jsondata["code"]=-4
                            jsondata["msg"]="Requested reply is not avaliable now"
                        else:
                            jsondata["code"]=200
                            jsondata["msg"]="ok"
                            if i["replytype"]!="text":
                                i["replyurl"]=getdownloadlink(i["replyurl"])
                            jsondata["reply"]=i
                            s=""
                            with open(filepath+"/"+openid+"/"+sidx+"/reply/"+ridx+"/basic.txt",'r') as f:
                                s=f.read()
                                l=list(s)
                                l[0]='1'
                                s=''.join(l)
                                f.close()
                            with open(filepath+"/"+openid+"/"+sidx+"/reply/"+ridx+"/basic.txt",'w') as f:
                                f.write(s)
                                f.close()
        return jsonify(jsondata)

@app.route('/setmine',methods=['GET'])
def setmine():
    if request.method=="GET":
        jsondata={"code":200,"msg":"ok"}
        myopenid=request.args.get('myopenid')
        openid=request.args.get('otheropenid')
        idx=request.args.get('storyidx')
        replyidx=request.args.get('replyidx')
        if not(os.path.exists(filepath+"/"+openid) or os.path.exists(filepath+"/"+myopenid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+str(idx))):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                if not(os.path.exists(filepath+"/"+openid+"/"+str(replyidx))):
                    jsondata["code"]=-3
                    jsondata["msg"]="No requested replyidx"
                else:
                    setreplymine(myopenid,openid,idx,replyidx)
        return jsonify(jsondata)

@app.route('/setglobal',methods=['GET'])
def setglobal():
    if request.method=="GET":
        jsondata={"code":200,"msg":"ok"}
        openid=request.args.get('openid')
        idx=request.args.get('storyidx')
        replyidx=request.args.get('replyidx')
        if idx=="a":
            return jsonify(jsondata)
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+str(idx))):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                if not(os.path.exists(filepath+"/"+openid+"/"+str(replyidx))):
                    jsondata["code"]=-3
                    jsondata["msg"]="No requested replyidx"
                else:
                    replys=[]
                    with open(filepath+"/globalstory.txt",'r') as g:
                        for fstr in g.readlines():
                            fstr=fstr.strip()
                            l=fstr.split(' ')
                            r=readreply(l[0],l[1])
                            for i in r:
                                if i["replyidx"]==str(l[2]):
                                    replys.append(i["openid"]+i["storyidx"]+i["replyidx"])
                        g.close()
                    if not (openid+idx+replyidx in replys):
                        with open(filepath+"/globalstory.txt",'a') as file:
                            file.write(openid+" "+idx+" "+replyidx+"\n")
        return jsonify(jsondata)

@app.route('/getgloballist',methods=['GET'])
def getgloballist():
    if request.method=="GET":
        jsondata={"code":200,"msg":"ok","replylist":[]}
        openid=request.args.get('openid')
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            replys=[]
            with open(filepath+"/globalstory.txt",'r') as g:
                for fstr in g.readlines():
                    fstr=fstr.strip()
                    l=fstr.split(' ')
                    r=readreply(l[0],l[1])
                    for i in r:
                        if i["replyidx"]==str(l[2]):
                            replys.append({"openid":i["openid"],"avaliabletime":i["avaliabletime"],"isavaliable":i["isavaliable"],"replyidx":i["replyidx"],"storyidx":i["storyidx"]})
                g.close()
            jsondata["replylist"]=replys
        return jsonify(jsondata)

@app.route('/clear',methods=['POST'])
def clear():
    if request.method=="POST":
        jsondata={"code":200,"msg":"ok"}
        result=json.loads(request.get_data(as_text=True))
        token=result['token']
        if token==config.OpenAIAPIKey:
            shutil.rmtree(filepath)
            if(not(os.path.exists(filepath))):
                os.makedirs(filepath)
            open(filepath+"/globalstory.txt",'w')
        else:
            jsondata["code"]=-1
            jsondata["msg"]="Token Error!"
        return jsonify(jsondata)

@app.route('/admingetreply',methods=['GET'])
def admingetreply():
    if request.method=="GET":
        jsondata={"code":-3,"msg":"No requested replyidx"}
        openid=request.args.get('openid')
        sidx=request.args.get('storyidx')
        ridx=request.args.get('replyidx')
        if not(os.path.exists(filepath+"/"+openid)):
            jsondata["code"]=-1
            jsondata["msg"]="No requested openid"
        else:
            if not(os.path.exists(filepath+"/"+openid+"/"+str(sidx))):
                jsondata["code"]=-2
                jsondata["msg"]="No requested storyidx"
            else:
                r=readreply(openid,sidx)
                for i in r:
                    if i["replyidx"]==str(ridx):
                        jsondata["code"]=200
                        jsondata["msg"]="ok"
                        if i["replytype"]!="text":
                            i["replyurl"]=getdownloadlink(i["replyurl"])
                        jsondata["reply"]=i
        return jsonify(jsondata)

if __name__=="__main__":
    #t=threading.Thread(target=getAccessToken,args=())
    #t.start()
    app.run(host='0.0.0.0',port=23333)
    #_async_raise(t.ident,SystemExit)
    print("Good bye!")