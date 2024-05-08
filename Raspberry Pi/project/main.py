import pyRTOS

def task1(test):
	while True:
		print("Test")
		yield [pyRTOS.timeout(1)]

def task2(test):

	while True:
		print("Task2")
		yield [pyRTOS.timeout(2)]

pyRTOS.add_task(pyRTOS.Task(task1, priority=0, name="touch"))
pyRTOS.add_task(pyRTOS.Task(task2, priority=1, name="color"))

pyRTOS.start()