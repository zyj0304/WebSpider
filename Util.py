import redis,time
from datetime import datetime,timedelta

r = redis.Redis(db=0,host='39.98.35.147', port=6379, decode_responses=True)

def formatTime():
    return time.strftime("%Y%m%d",time.localtime())

def yesterday():
    return (datetime.now()-timedelta(days=1)).strftime("%Y%m%d")

def curTime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def logTask(ip,lanmuId,status):
    r.hset("scheduler:note:day:"+formatTime()+":"+ip+":"+lanmuId,curTime(),status)

def getTaskJavaId(q):
    '''
    获得java的id
    :return:
    '''
    return r.rpop("scheduler:task:%s" % q)


def checkKillNodeTask(ip):
    return r.exists("scheduler:note:kill:"+ip)

def getKillNodeTask(ip):
    lanmuId=r.get("scheduler:note:kill:"+ip)
    return lanmuId

def checkCollectNodeLog(ip):
    return r.exists("scheduler:note:log:"+ip)

def checkTaskCurQueueExist(ip,lanmuId):
    '''
    当前ip的活跃节点是否存在
    :return:
    '''
    return r.exists("scheduler:note:cur:"+ip+":"+lanmuId)

def checkTaskDayQueueExist(ip):
    '''
    当天任务分发节点是否存在
    :param ip:
    :return:
    '''
    return r.exists("scheduler:note:day:"+ip)

def getAllIPKey(lanmuId):
    keys=r.keys("scheduler:note:cur:*:"+lanmuId)
    res=[]
    for key in keys:
        res.append(key.replace("scheduler:note:cur:","").replace(":"+lanmuId,""))
    return res

def getAllNode():
    keys=r.keys("scheduler:note:cur:*")
    res=[]
    for key in keys:
        res.append(key.replace("scheduler:note:cur:",""))
    return res

def getAllRunLog(lanmuId):
    '''
    运行日志
    :return:
    '''
    keys=r.keys("scheduler:note:day:*"+lanmuId)
    res=[]
    for key in keys:
        res.append(key)
    res.sort(reverse=True)
    results={}
    for item in res[0:100]:
        arr=item.split(":")
        for key,value in r.hgetall(item).items():
            results.setdefault(arr[3],[]).append(arr[4]+":"+key+":"+value)
    return results

def clearAllLog():
    keys=r.keys("log:*")
    for key in keys:
        r.ltrim(key,1,1000)

if __name__=="__main__":
    #print(getAllRunLog("654a6fg465ds4"))
    #r.hset("scheduler:note:day:20200716:127.0.0.1:654a6fg465ds4", curTime(), "stop")
    #rint(r.exists("scheduler:log:do:127.0.0.1"))
    #clearAllLog()
    print(yesterday())