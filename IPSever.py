import requests,json
import socket
from Util  import r
import random

def getIpPort(num:int) ->list :
    '''
    获得芝麻代理的ip
    :param num:
    :return:
    num=6&type=2&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=45&mr=2&regions=&gm=4
    '''
    data={"num":num,"type":2,"pro":"","city":0
          ,"yys":0,"port":1,"time":1,"ts":0
          ,"ys":0,"cs":0,"lb":1,"sb":0,"pb":45
          ,"mr":2,"regions":"","gm":4}
    response=requests.get("http://http.tiqu.alicdns.com/getip3",data)
    results=json.loads(response.text)
    for items in results["data"]:
        r.hset("ip:pool",items["ip"],items["port"])
    return results["data"]

#[{'ip': '58.218.92.198', 'port': 8465, 'outip': '58.45.101.209'}, {'ip': '58.218.92.197', 'port': 9917, 'outip': '49.64.64.218'}]

def testPort(ip:str,port:int):
    '''
    测试已有的ip是否过期
    :param ip:
    :param port:
    :return:
    '''
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(20)
    try:
        sk.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        sk.close()

def getCurUserIp(num:int,nFlag=False):
    '''
    :param num: 需要ip的个数
    :param nFlag: 只要全新的ip
    :return:
    '''
    if nFlag:
        return getIpPort(num)
    else:
        ipPort=getRedisIps()
        if num<=len(ipPort):
            random.shuffle(ipPort)
            return ipPort[:num]
        else:
            doNum=num-len(ipPort)
            ips=getIpPort(doNum)
            return ips+ipPort

def getRedisIps():
    '''
    获得redis现存可使用ip
    :return:
    '''
    dics=r.hgetall("ip:pool")
    res=[]
    for key,value in dics.items():
        res.append({"ip":key,"port":int(value)})
    return res

def rmUserLessIps():
    dics=r.hgetall("ip:pool")
    res=[]
    for key,value in dics.items():
        res.append({"ip":key,"port":int(value)})
        if not testPort(key,int(value)):
            print("移除 %s %s 代理ip" % (key,value))
            r.hdel("ip:pool",key)

if __name__=="__main__":
    rmUserLessIps()
    #print(getCurUserIp(2))

