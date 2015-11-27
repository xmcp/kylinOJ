#coding=utf-8

DEBUG=True

VM_NAME='JudgementVM'
VM_BASE_SNAPSHOT='JVM 1.1'
VM_ROOT_PSW='NiNaliExpl0de**lema? '
VM_JUDGE_PSW='INT_MAX==2147483647;'

def init_vbox_svr():
    import os, time
    os.system(r'start "" /min "C:\Program Files\Oracle\VirtualBox\VBoxWebSrv.exe"')
    print('=== Initialized VBox Server')
    time.sleep(.5)

