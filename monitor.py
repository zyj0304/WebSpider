from Util import r,yesterday
from datetime import datetime,timedelta
from numpy import mean
from model import Configure,DBSession
import json

runHolds=10

def getTodayNode(day:str):
    keys=r.keys("scheduler:note:day:"+day+"*")
    res=set()
    for key in keys:
        ks=key.split(":")[4]
        res.add(ks)
    return res

def getTodayTask(day:str):
    '''
    获得当日所有运行栏目id
    :param day:
    :return:
    '''
    keys=r.keys("scheduler:note:day:"+day+"*")
    res=set()
    for key in keys:
        ks=key.split(":")[-1]
        res.add(ks)
    return res

def getIpNode(ip:str,day:str):
    keys = r.keys("scheduler:note:day:"+day +":"+ip+"*")
    res=[]
    for key in keys:
        res.append(key)
    res.sort(reverse=False)
    return res

def getLanmuIdTask(lanmuId:str):
    keys = r.keys("scheduler:note:day:*"+lanmuId)
    res=[]
    for key in keys:
        res.append(key)
    res.sort(reverse=False)
    return res

def monitorTask():
    '''
    检测任务运行情况
    :return:
    '''
    day=yesterday()
    lanmuIds=getTodayTask(day)
    results={}
    for lanmuId in lanmuIds:
        runTimes=[]
        res=getLanmuIdTask(lanmuId)
        if len(res)<5:
            continue
        for item in res:
            runTimes.append(getRunTimes(item))
        print(runTimes)
        cMax=max(runTimes)
        #cMin=min(runTimes)
        cMean=mean([v for v in runTimes if v<cMax])
        if cMean<runHolds:
            results[lanmuId]="运行时间过短,请检查程序是否正常"
        lMean=mean([v for v in runTimes[-3:] if v<cMax])
        if lMean<cMean*1.0/3:
            results[lanmuId] = "最近三天运行时间比平均运行时间三分之一还少,请检查程序是否正常"
    r.hset("scheduler:check:task",day,json.dumps(getAllTask(results),ensure_ascii=False))

def getAllTask(results:dict):
    session = DBSession()
    tasks = session.query(Configure.lanmuId,Configure.lanmuName,Configure.detailUrl,Configure.userName).all()
    res=[]
    for item in tasks:
        #res.append({"id":str(item.id),"cron":item.cron,"abandon":item.abandon,"cType":1,"machines":item.machines,"lanmuName":item.lanmuName,"lanmuId":item.lanmuId})
        if item.lanmuId in results:
            res.append({"lanmuId":item.lanmuId,"lanmuName":item.lanmuName,"detailUrl":item.detailUrl,
                        "userName":item.userName,"status":results[item.lanmuId]})
    session.close()
    return res

def getRunTimes(key:str):
    keys=r.hgetall(key)
    try:
        if len(keys)==2:
            items={v:k for k,v in keys.items()}
            start=datetime.strptime(items['start'],"%Y-%m-%d %H:%M:%S")
            finish=datetime.strptime(items['finish'],"%Y-%m-%d %H:%M:%S")
            return (finish-start).seconds
    except:
        pass
    return 3600

def monitorNode():
    day=yesterday()
    ips=getTodayNode(day)
    print(ips)
    results = {}
    for ip in ips:
        runTimes = []
        res=getIpNode(ip,day)
        if len(res)<2:
            continue
        for item in res:
            runTimes.append(getRunTimes(item))
        cMean=mean([v for v in runTimes if v!=3600])
        print(cMean)
        if cMean<runHolds:
            results[ip] = cMean
    r.hset("scheduler:check:node", day, json.dumps(results, ensure_ascii=False))

if __name__=="__main__":
    monitorNode()