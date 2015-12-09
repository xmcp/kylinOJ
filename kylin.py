#coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
os.chdir(os.path.split(__file__)[0])

import const
import time
import threading
import vboxapi
import pywintypes
from contextlib import closing

def wait(sth):
    if sth is not None:
        sth.waitForCompletion(-1)

class Result:
    CE='Compile Error'
    RE='Runtime Error'
    LE='Limit Excedded'
    WA='Wrong Answer'
    PE='Presentation Error'
    SB='System Bug'
    AC='Accepted'

class Kylin:
    mgr=vboxapi.VirtualBoxManager()
    vbox=mgr.vbox

    def __init__(self,vm_name,log):
        self.log=log
        self.vm_name=vm_name
        self.log('=== initializing')
        self.vm=self.vbox.findMachine(vm_name)
        self.session=self.mgr.getSessionObject(self.vbox)
        self.running=False

    def _boot(self):
        self.vm=self.vbox.findMachine(self.vm_name)
        self.session=self.mgr.getSessionObject(self.vbox)
        self.log('  === launching')
        while True:
            try:
                wait(self.vm.launchVMProcess(self.session,'gui' if const.DEBUG else 'headless',''))
            except pywintypes.com_error: #still unlocking machine
                time.sleep(.1)
            else:
                break
        self.log('  === waiting for gs')
        while True:
            try:
                result=self._execute('judge',const.VM_JUDGE_PSW,'/bin/echo',['hello','world'],2)
                assert result[0]==0 and result[1].startswith('hello world') and not result[2]
            except (AssertionError,pywintypes.com_error):
                time.sleep(.1)
            else:
                break

    def _execute(self,user,passwd,program,args,timeout=15,stdin=None):
        def read_out():
            process.waitFor(7,0)
            o=process.read(1,65000,0).tobytes().decode('utf-8','ignore')
            stdout.append(o)
            process.waitFor(8,0)
            e=process.read(2,65000,0).tobytes().decode('utf-8','ignore')
            stderr.append(e)

        timeout*=1000
        if self.session.state==1:
            self.session=self.mgr.openMachineSession(self.vm)

        self.log('  === creating process')
        with closing(self.session.console.guest.createSession(user,passwd,"","kylinOJ execute session")) as gs:
            while gs.status!=100:
                time.sleep(.02)
            process=gs.processCreate(program,[program]+args,[],[16,32],timeout)
            process.waitFor(1,0)

            if stdin:
                self.log('  === writing stdin')
                process.waitFor(4,0)
                index=0
                while index<len(stdin):
                    array=list(map(lambda a:str(ord(a)),stdin[index:]))
                    wrote=process.writeArray(0,[0],array,0)
                    if not wrote:
                        if process.status<=100:
                            raise RuntimeError('Failed to write ANY bytes to STDIN')
                        else: #terminated
                            break
                    index+=wrote
                process.writeArray(0,[1],[],0)

            self.log('  === executing')
            stdout,stderr=[],[]
            while process.status<=100:
                read_out()
                time.sleep(0.02)
            self.log('  === stopped')
            read_out()

            return process.exitCode,''.join(stdout),''.join(stderr)

    def _writefile(self,user,passwd,filename,content):
        if self.session.state==1:
            self.session=self.mgr.openMachineSession(self.vm)

        self.log('  === initializing gs')
        with closing(self.session.console.guest.createSession(user,passwd,"","kylinOJ writefile session")) as gs:
            while gs.status!=100:
                time.sleep(.02)
            self.log('  === writing')
            with closing(gs.fileOpen(filename,2,4,0x755)) as handler:
                handler.write(content.encode('utf-8','ignore'),1000)

    def restore(self):
        def _pwn():
            self.log('  === writing judger')
            with open('vm_files/judger.cpp','r') as f:
                self._writefile('root',const.VM_ROOT_PSW,'/root/judger.cpp',f.read().replace('/*JUDGE_UID*/',const.VM_JUDGE_UID))

            self.log('  === compiling judger')
            code,out,err=self._execute('root',const.VM_ROOT_PSW,'/usr/bin/g++',['-o','/root/judger','/root/judger.cpp'])
            if code:
                self.log('!!! errcode = %d'%code)
                self.log('[STDOUT]\n%s\n[STDERR]\n%s'%(out,err))

        if self.session.state!=1:
            self.log('=== powering down')
            wait(self.session.console.powerDown())
        while self.session.state!=1:
            time.sleep(.1)

        self.log('=== opening session')
        self.session=self.mgr.openMachineSession(self.vm)
        self.vm=self.session.machine
        self.log('=== restoring')
        wait(self.vm.restoreSnapshot(self.vm.findSnapshot(const.VM_BASE_SNAPSHOT)))
        wait(self.session.unlockMachine())

        self.log('=== powering up')
        while self.session.state!=1:
            time.sleep(.1)
        self._boot()
        _pwn()

    def _real_judge(self,source,memlimit,timelimit,datas,callback):
        results=[]
        callback({'progress':'init'})
        self.restore()
        try:
            self.log('=== copying user program')
            self._writefile('judge',const.VM_JUDGE_PSW,'/home/judge/program.cpp',source)

            callback({'progress':'compiling'})
            self.log('=== compiling')
            code,out,err=self._execute('judge',const.VM_JUDGE_PSW,'/usr/bin/g++',['-static','-o','/home/judge/program','/home/judge/program.cpp'])
            if code:
                self.log('!!! errcode = %d'%code)
                self.log('[STDOUT]\n%s\n[STDERR]\n%s'%(out,err))
                return callback({'progress':'done','result':[Result.CE]})

            len_datas=len(datas)
            for pos,io in enumerate(datas):
                callback({'progress':'judging','result':results})
                self.log('=== judging data %d/%d'%(pos+1,len_datas))

                code,out,err=self._execute('root',const.VM_ROOT_PSW,'/root/judger',[memlimit*1024*1024,timelimit],timelimit+1,io[0])
                if const.DEBUG:
                    self.log('[ERRCODE] %d\n[STDOUT]\n%s\n[STDERR]\n%s'%(code,out,err))

                if code and err.startswith('[JUDGER ERROR] '):
                    results.append(Result.SB)
                elif code:
                    results.append(Result.RE)
                elif not out:
                    results.append(Result.WA)
                elif [x.rstrip() for x in out.rstrip().splitlines()]==[x.rstrip() for x in io[1].rstrip().splitlines()]:
                    results.append(Result.AC)
                elif out.replace(' ','').replace('\n','')==io[1].replace(' ','').replace('\n',''):
                    results.append(Result.PE)
                else:
                    results.append(Result.WA)
        except Exception as e:
            self.log('!!! Uncaught Error: %r'%e)
            return callback({'progress':'done','result':results+[Result.SB]})
        else:
            return callback({'progress':'done','result':results})
        finally:
            self.running=False

    def judge(self,*args):
        self.running=True
        threading.Thread(target=self._real_judge,args=args).start()

class MultiKylin:
    def __init__(self,log):
        log('= initializing kylins')
        self.kylins=[Kylin(name,log) for name in const.VMS]

    def judge(self,*args):
        while True:
            for kylin in self.kylins:
                if not kylin.running:
                    return kylin.judge(*args)
            time.sleep(.25)

if __name__=='__main__':
    lock=threading.Lock()
    def wrapper(cnt):
        def callback(data):
            with lock:
                print('[%d] %s'%(cnt,data))

        return callback

    kylin=MultiKylin(print if const.DEBUG else lambda *_:None)
    #xx=kylin._execute('root',const.VM_ROOT_PSW,'/bin/echo',['foo','bar'],30)
    #xx=kylin._writefile('root',const.VM_ROOT_PSW,'/root/foo.bar','hello world!')
    for _ in range(3):
        kylin.judge(
            '#include<cstdio>\nint main(){int a,b;scanf("%d%d",&a,&b);printf("%d",a+b);}',
            10, #mem MB
            1, #time second
            [['1 2','3'],['4 5','9']], #datas
            wrapper(_)
        )