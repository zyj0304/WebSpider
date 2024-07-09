FROM python:3.8

# 设置工作目录
WORKDIR /app
# 复制代码
COPY . /app

RUN pip install --upgrade pip
# 安装依赖
RUN pip install -r requirements.txt


# 暴露端口
#EXPOSE 8000
# 启动命令
CMD ["python", "test.py"]
#CMD ["python", "test.py", "1>server.log", "2>server.log"]
#CMD python test.py > /app/output.log 2>&1
#CMD "python test.py  > /app/output.log 2>&1"
