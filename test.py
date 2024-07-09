
import time
import logging
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                        level=logging.DEBUG,
                        filename='test.log',
                        filemode='a')
    for i in range(50000):
        logging.info(i)
        print('第'+str(i)+'个>>>>>')
        time.sleep(2)

