import time
import inspect

def lineno():
    """    이 함수를 호출한 곳의 라인번호를 리턴한다.    """
    return inspect.getlineno(inspect.getouterframes(inspect.currentframe())[-1][0])
start = time.time()
msg = '{0}, line: {1}, lap-time: {2:.3f}'
print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()
aaa = 100

print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()

bbb = 1000

time.sleep(0.123)

print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()

time.sleep(0.222)
aaa = 100

print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()

aaa = 100

print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()

time.sleep(1.222)
aaa = 100
print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()

time.sleep(2.3333333)
aaa = 100
print(msg.format(__file__.split('/')[-1], lineno(), time.time()-start))
start = time.time()
