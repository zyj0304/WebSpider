
from flask import Flask,request,jsonify,render_template,Response,session,redirect
import flask_excel as excel
import base64,hashlib,time,json
from model import Configure,DBSession,username,desc,or_
from Util  import getTaskJavaId,checkTaskCurQueueExist,r,checkKillNodeTask,getKillNodeTask,getAllIPKey,logTask,getAllNode,curTime,getAllRunLog,yesterday
from functools import wraps
from IPSever import getCurUserIp

application = Flask(__name__)
application.secret_key = "sdfasdfasdf3fsdf"
excel.init_excel(application)
store=[]
#storeNode={}#存储节点

def wapper(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if not session.get('user_info'):
            return redirect('/login')
        return func(*args,**kwargs)
    return inner

@application.route('/getCheckTask',methods=['GET'])
def getCheckTask():
    res=json.loads(r.hget("scheduler:check:task",yesterday()))
    return render_template("checkTask.html",results=res)

@application.route('/getCheckNode',methods=['GET'])
def getCheckNode():
    res=json.loads(r.hget("scheduler:check:node",yesterday()))
    return render_template("checkNode.html",results=res)

@application.route('/getProper',methods=['GET'])
def getProper():
    '''
    返回访问得ip地址
    :return:
    '''
    lanmuId = request.args.get("lanmuId")
    key = request.args.get("key")
    if r.hexists("proper:"+lanmuId,key):
        return r.hget("proper:"+lanmuId,key)
    else:
        return "1"

@application.route('/setProper',methods=['GET'])
def setProper():
    '''
    返回访问得ip地址
    :return:
    '''
    lanmuId = request.args.get("lanmuId")
    key = request.args.get("key")
    value = request.args.get("value")
    r.hset("proper:"+lanmuId,key,value)
    return "success"

@application.route('/getLocalIp',methods=['GET'])
def getLocalIp():
    '''
    返回访问得ip地址
    :return:
    '''
    return request.remote_addr

@application.route('/getIps',methods=['POST','GET'])
def getIps():
    num=request.args.get("num")
    new=request.args.get("new")
    if num==None:
        return jsonify({"msg":"num字段不能为空"})
    num=int(num)
    if new!=None and new=="yes":
        res=getCurUserIp(num,True)
    else:
        res=getCurUserIp(num)
    return jsonify(res)

@application.route('/login',methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        user = request.form.get('username')
        pwd = request.form.get('password')
        if haveUserOrPwd(user,pwd):
            session['user_info'] = user
            print("登录成功")
            return redirect('/')
        else:
            return render_template('login.html',warning='用户或密码错误')

def haveUserOrPwd(user,pwd):
    session=DBSession()
    tasks = session.query(username).filter(username.name==user,username.pwd==pwd).all()
    session.close()
    return len(tasks)>0

def getMd5(data):
    return hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()

def sNode(ip:str):
    r.hset("scheduler:note:all",ip,curTime())

@application.route('/getTask',methods=['POST','GET'])
def getTask():
    '''
    task 1为java任务
         2为配置任务
         3为当前任务为空
         4为结束指定任务
         5为收集日志
         6为暂停收集日志
    :return:
    '''
    ip = request.remote_addr
    sNode(ip)
    if checkKillNodeTask(ip):
        lanmuId=getKillNodeTask(ip)
        r.delete("scheduler:note:kill:"+ip)
        r.delete("scheduler:note:cur:"+ip+":"+lanmuId)
        logTask(ip, lanmuId, "stop")
        return jsonify({"task":4,"lanmuId":lanmuId})
    #收集采集日志
    #检测其他
    doNotWantATask= request.args.get("doNotWantATask")
    if doNotWantATask!=None:
        return jsonify({"task":3})
    id=None
    #selenium任务
    doSelenium=request.args.get("doSelenium")
    if doSelenium=="yes":
        id = getTaskJavaId("seleniumQueue")
    if id==None:
        id = getTaskJavaId("javaQueue")
    if id!=None:
        t=taskJava(int(id))
        if not checkTaskCurQueueExist(ip,t["lanmuId"]):
            r.set("scheduler:note:cur:%s:%s" % (ip,t["lanmuId"]), "1122")
            logTask(ip, t["lanmuId"], "start")
            return jsonify({"task":1,"data":t})
        else:
            r.lpush("scheduler:task:javaQueue",id)
    return jsonify({"task":3})

def checkLog(ip):
    ips=r.hgetall("scheduler:log")
    if ip in ips:
        if int(time.time())-int(ips[ip])>30:
            r.hdel("scheduler:log",ip)
            r.delete("scheduler:log:do:"+ip)
            return 2
        else:
            if not r.exists("scheduler:log:do:"+ip):
                r.set("scheduler:log:do:"+ip,"")
                return 1
    else:
        return 0

def storeMsg(ip,msg):
    r.lpush("scheduler:msg:"+ip,msg)

def getStoreMsg(ip):
    res=[]
    for i in range(10):
        if r.llen("scheduler:msg:"+ip)>0:
            res.append(r.lpop("scheduler:msg:"+ip))
        else:
            break
    return res

@application.route("/getMsg",methods=['POST','GET'])
def getMsg():
    ip = request.args.get("ip")
    msg=getStoreMsg(ip)
    r.hset("scheduler:log",ip,int(time.time()))#
    return jsonify(msg)

@application.route("/msg",methods=['POST','GET'])
def msg():
    msg = request.args.get("msg")
    ip = request.remote_addr
    storeMsg(ip,msg)
    return jsonify({"status":"success"})

@application.route("/getMsgContent",methods=['POST','GET'])
def getMsgContent():
    ip = request.args.get("ip")
    return render_template("msg.html",ip=ip)

@application.route("/getLog",methods=['POST','GET'])
def getLog():
    lanmuId = request.args.get("lanmuId")
    if r.llen("log:"+lanmuId)>0:
        ls=r.lrange("log:"+lanmuId,0,1000)
        query_sets=[]
        for line in ls:
            arr=[x for x in line.split(">>>")]
            query_sets.append(arr)
        title=['ip', 'time', 'msg']
        return excel.make_response_from_query_sets(query_sets=query_sets,column_names=title,file_type='xls',file_name=lanmuId+'.xls')
    else:
        #return jsonify({"status":"当前栏目无日志，请确定当前爬虫继承了com.lexlang.WebSpider.log包下Log类，并使用log方法记录日志"})
        return render_template("alertLog.html")

@application.route("/finishLanmuId",methods=['POST','GET'])
def finishLanmuId():
    lanmuId = request.args.get("lanmuId")
    ip = request.remote_addr
    r.delete("scheduler:note:cur:" + ip + ":" + lanmuId)
    logTask(ip, lanmuId, "finish")
    return jsonify({"status":"success"})

@application.route("/stopLanmuId",methods=['POST','GET'])
def stopLanmuId():
    lanmuId = getLanmuId(request.args.get("id"))
    cHand=int(request.args.get("cHand"))
    if cHand==0:
        ips=getAllIPKey(lanmuId)
        for ip in ips:
            r.set("scheduler:note:kill:"+ip,lanmuId)
    else:
        #startTask(lanmuId)
        pass
    #更改数据库内容
    if changeStore(lanmuId,cHand):
        changeStore(lanmuId,cHand)
    return jsonify({"status":"success"})

@application.route("/runTask",methods=['POST','GET'])
def runTask():
    lanmuId = getLanmuId(request.args.get("id"))
    startTask(lanmuId)
    return jsonify({"status": "success"})

def startTask(lanmuId:str):
    id, machines = getId(lanmuId)
    queue = checkTaskType(id)
    for i in range(int(machines)):
        r.lpush("scheduler:task:" + queue, id)


@application.route("/getJavaDetail",methods=['POST','GET'])
@wapper
def getJavaDetail():
    id = request.args.get("id")
    return Response(getJava(id), mimetype='text/plain')

def getLanmuId(id):
    session=DBSession()
    task = session.query(Configure.lanmuId).filter(Configure.id==id).all()[0]
    id=task.lanmuId
    session.close()
    return id

def changeStore(lanmuId,abandon):
    session=DBSession()
    session.query(Configure).filter(Configure.lanmuId==lanmuId).update({"abandon":(0 if abandon>0 else 1)})
    session.commit()
    session.close()

def getId(lanmuId):
    session=DBSession()
    task = session.query(Configure.id,Configure.machines).filter(Configure.lanmuId==lanmuId).all()[0]
    res=task.id,task.machines
    session.close()
    return res

def getJava(id):
    session=DBSession()
    task = session.query(Configure).filter(Configure.id==id).all()[0]
    if task.java.startswith('{'):
        results=json.loads(task.java)
        if results["cType"]==1:
            res=task.java
        elif results["cType"]==2:
            res=results["javaScript"]
    else:
        res=base64.b64decode(task.java.encode()).decode()
    session.close()
    return res

@application.route('/changeFile',methods=['POST','GET'])
@wapper
def changeFile():
    lanmuId = request.form['lanmuId']
    sFile = request.files.get("file").read()
    eFile = base64.b64encode(sFile).decode()
    updateChangeFile(lanmuId, eFile)
    return jsonify({"status":"success"})

def updateChangeFile(lanmuId:str,eFile:str):
    session = DBSession()
    session.query(Configure).filter(Configure.lanmuId==lanmuId).update({"java":eFile})
    session.commit()
    session.close()

@application.route('/addJavaTask',methods=['POST','GET'])
@wapper
def addJavaTask():
    name=session['user_info']
    if request.method=='POST':
        sFile=request.files.get("file").read()
        lanmuId = request.form['lanmuId']
        lanmuName=request.form['lanmuName']
        if lanmuName==None:
            lanmuName=""
        eFile = base64.b64encode(sFile).decode()
        if lanmuId == None or len(lanmuId) < 2:
            lanmuId=getMd5(lanmuName+eFile)
        insertJavaTask(lanmuId,
                   request.form['lanmuName'],
                   request.form['detailUrl'],
                   eFile,
                   request.form['cron'],
                   request.form['machines']
                   ,name)
    return render_template('addTask.html',mark="Java")

@application.route('/addPara',methods=['POST','GET'])
@wapper
def addPara():
    name = session['user_info']
    if request.method=='POST':
        sFile=request.files.get("file").read()
        lanmuId = request.form['lanmuId']
        lanmuName=request.form['lanmuName']
        cron=request.form['cron']
        machines=request.form['machines']
        detailUrl = request.form['url']
        lastPageUrl = request.form['lastPageUrl']
        lastPageMatch = request.form['lastPageMatch']
        if len(sFile)<1:
            res={}
            res["cType"]=1
            res["url"]= request.form['url']
            res["startInt"]= int(request.form['startInt'])
            res["lastInt"] = int(request.form['lastInt'])
            if len(request.form['crawlSucessMark']) > 0:
                res["crawlSucessMark"] = request.form['crawlSucessMark']
            if len(request.form['detailRegular'])>0:
                res["detailRegular"] = request.form['detailRegular']
            if lastPageMatch!=None and len(lastPageMatch)>1:
                res["lastPageMatch"]=lastPageMatch
                res["lastPageUrl"] = lastPageUrl
            f=json.dumps(res,ensure_ascii=False)
        else:
            res={}
            res["cType"]=2
            res["javaScript"]=sFile.decode()
            if lastPageMatch!=None and len(lastPageMatch)>1:
                res["lastPageMatch"]=lastPageMatch
                res["lastPageUrl"] = lastPageUrl
            f=json.dumps(res,ensure_ascii=False)
        if lanmuId==None or len(lanmuId)<3:
            lanmuId=getMd5(lanmuName+f)
        insertJavaTask(lanmuId,
                       lanmuName,
                       detailUrl,
                       f,
                       cron,
                       machines,
                       name)
    return render_template('addPara.html',mark="配置")

@application.route('/searchTask',methods=['POST','GET'])
@wapper
def searchTask():
    if request.method == 'POST':
        detailUrl = request.form['detailUrl']
        results =[]
        if detailUrl!=None:
            results,total=task(detailUrl)
        return render_template('searchTask.html',results=results,pageConfig={},total=total,pageNo=0)
    else:
        pageNo=request.args.get("pageNo")
        if pageNo==None:
            pageNo=0
        else:
            pageNo=int(pageNo)
            if pageNo<0:
                pageNo=0
        results,total=searchPageNoTask(pageNo)
        pageConfig={"beforePage":pageNo-10,"nextPage":pageNo+10}
        return render_template('searchTask.html',results=results,pageConfig=pageConfig,total=total,pageNo=pageNo)

@application.route('/searchNode',methods=['POST','GET'])
@wapper
def searchNode():
    ips=getAllNode()
    lanmuIdNames=getLanmuIdName()
    results={}
    for ip in ips:
        arr=ip.split(":")
        if arr[1] in lanmuIdNames.keys():
            results.setdefault(arr[0],[]).append(lanmuIdNames[arr[1]])
    for key,value in getAllStoreNode().items():
        results.setdefault(key, []).append(value)
    return render_template('searchNode.html',results=results)

def getAllStoreNode():
    return r.hgetall("scheduler:note:all")

@application.route('/clearAllTask',methods=['POST','GET'])
def clearAllTask():
    keys = r.keys("scheduler:note:cur:*")
    for key in keys:
        r.delete(key)
    return jsonify({"status": "success"})

@application.route('/',methods=['POST','GET'])
@wapper
def index():
    return render_template("index.html")

@application.route('/checkCrawlLog',methods=['POST','GET'])
def checkCrawlLog():
    lanmuId = request.args.get("lanmuId")
    results=getAllRunLog(lanmuId)
    return render_template("crawlLog.html",results=results)

def insertJavaTask(lanmuId,lanmuName,detailUrl,eFile,cron,machines,userName):
    '''
    插入数据
    :param lanmuId:
    :param cType:
    :param eFile:
    :return:
    '''
    session = DBSession()
    task=Configure(lanmuId=lanmuId
                   ,lanmuName=lanmuName
                   ,detailUrl=detailUrl
                   ,java=eFile
                   ,cron=cron
                   ,machines=machines
                   ,userName=userName)
    session.add(task)
    session.commit()
    session.close()

def searchPageNoTask(pageNo:int):
    session=DBSession()
    total=len(session.query(Configure.id).all())
    tasks=session.query(Configure).order_by(desc(Configure.id)).offset(pageNo).limit(10).all()
    results=[]
    for item in tasks:
        java=item.java
        cType=0
        if java.startswith('{'):
            jResults=json.loads(java)
            cType=jResults["cType"]
        res={"lanmuId":item.lanmuId
           ,"lanmuName":item.lanmuName
           ,"detailUrl":item.detailUrl
           ,"java":item.java
           ,"cron":item.cron
           ,"machines":item.machines
           ,"abandon":(item.abandon if item.abandon!=None else 0)
           ,"id":item.id
           ,"cType":cType
           ,"userName":item.userName}
        results.append(res)
    session.close()
    return results,total

def taskJava(id:int):
    session = DBSession()
    tasks = session.query(Configure).filter(Configure.id==id).all()
    for item in tasks:
        res={"lanmuId":item.lanmuId
                   ,"lanmuName":item.lanmuName
                   ,"detailUrl":item.detailUrl
                   ,"java":item.java
                   ,"cron":item.cron
                   ,"machines":item.machines
                   ,"abandon":(item.abandon if item.abandon!=None else 0)
                   ,"id":item.id}
        return res
    session.close()
    return {}

def checkTaskType(id:int):
    if r.hexists("scheduler:queue",str(id)):
        return r.hget("scheduler:queue",str(id))
    res=taskJava(id)
    java=res["java"]
    if java.startswith("{"):
        if "lastPageMatch" in java:
            storeTaskType(id, "seleniumQueue")
            return "seleniumQueue"
        else:
            storeTaskType(id, "javaQueue")
            return "javaQueue"
    else:
        eFile=base64.b64decode(java.encode()).decode()
        if "SearchLastPageNo" in eFile or "SeleniumRequests" in eFile or "WebDriver" in eFile:
            storeTaskType(id, "seleniumQueue")
            return "seleniumQueue"
        else:
            storeTaskType(id, "javaQueue")
            return "javaQueue"

def storeTaskType(id:int,queue:str):
    r.hset("scheduler:queue",str(id),queue)

def getLanmuIdName():
    session = DBSession()
    tasks = session.query(Configure.lanmuId,Configure.lanmuName).all()
    res={}
    for item in tasks:
        res[item.lanmuId]=item.lanmuName
    session.close()
    return res

def task(detailUrl=None):
    session=DBSession()
    if detailUrl!=None:
        tasks = session.query(Configure).filter(or_(Configure.detailUrl.like("%"+ detailUrl+"%"),Configure.lanmuName.like("%"+ detailUrl+"%"))).limit(10).all()
    else:
        tasks=session.query(Configure).all()
    results=[]
    for item in tasks:
        java=item.java
        cType=0
        if java.startswith('{'):
            jResults=json.loads(java)
            cType=jResults["cType"]
        res={"lanmuId":item.lanmuId
               ,"lanmuName":item.lanmuName
               ,"detailUrl":item.detailUrl
               ,"java":java
               ,"cron":item.cron
               ,"machines":item.machines
               ,"abandon":(item.abandon if item.abandon!=None else 0)
               ,"id":item.id
               ,"userName":item.userName
               ,"cType":cType}
        results.append(res)
    session.close()
    return results,len(results)

if __name__=="__main__":
    application.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)