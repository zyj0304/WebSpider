from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from model import Configure,DBSession
import time
from Util import r,clearAllLog
from IPSever import rmUserLessIps
from Sever import checkTaskType
from monitor import monitorNode,monitorTask

store={}

sched = BackgroundScheduler()

def getAllTask():
    session = DBSession()
    tasks = session.query(Configure.id,Configure.lanmuName,Configure.cron,Configure.abandon,Configure.machines,Configure.lanmuId).all()
    res=[]
    for item in tasks:
        res.append({"id":str(item.id),"cron":item.cron,"abandon":item.abandon,"cType":1,"machines":item.machines,"lanmuName":item.lanmuName,"lanmuId":item.lanmuId})
    session.close()
    return res

def removeQueue():
    res=getAllTask()
    for item in res:
        if str(item["id"]) in store:
            try:
                flag=str(item["cron"])+str(item["abandon"])
                if flag!=store[str(item["id"])]:
                    try:
                        sched.remove_job(job_id=str(item["id"]))
                    except:
                        pass
                    store[str(item["id"])] = str(item["cron"]) + str(item["abandon"])
                    if item["abandon"]!=1 and item["cron"]!=None and len(item["cron"])>5:
                        sched.add_job(id=str(item["id"]), func=sendRedis, args=[item, ]
                                      , trigger=CronTrigger.from_crontab(item["cron"]))
            except:
                pass
        else:
            try:
                store[str(item["id"])] = str(item["cron"]) + str(item["abandon"])
                if item["abandon"] != 1 and item["cron"] != None and len(item["cron"]) > 5:
                    sched.add_job(id=str(item["id"]), func=sendRedis, args=[item, ]
                                  , trigger=CronTrigger.from_crontab(item["cron"]))
            except:
                pass

def addQueue():
    try:
        res=getAllTask()
        for item in res:
            try:
                store[str(item["id"])]=str(item["cron"])+str(item["abandon"])
                if item["abandon"]!=1 and item["cron"]!=None and len(item["cron"])>5:
                    print(item)
                    sched.add_job(id=str(item["id"]),func=sendRedis,args=[item,],trigger=CronTrigger.from_crontab(item["cron"]))
            except:
                pass
    except:
        pass

def sendRedis(item:dict):
    while not sendRed(item):
        time.sleep(2)

def sendRed(item:dict) -> bool:
    try:
        queue = checkTaskType(item["id"])
        for i in range(item["machines"]):
            r.lpush("scheduler:task:"+queue,item["id"])
        return True
    except:
        return False

if __name__=="__main__":
    addQueue()
    sched.add_job(rmUserLessIps, 'interval', seconds=10)
    sched.add_job(clearAllLog, 'interval', seconds=60*3)
    sched.add_job(func=monitorTask,  trigger=CronTrigger.from_crontab("* 1,2 * * *"))
    sched.add_job(func=monitorNode, trigger=CronTrigger.from_crontab("* 1,2 * * *"))
    sched.start()
    while True:
        time.sleep(60*60)
        try:
            removeQueue()
        except:
            pass
