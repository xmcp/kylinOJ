#coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
os.chdir(os.path.split(__file__)[0])

import const
import time
import vboxapi
import pywintypes
from contextlib import closing

def wait(sth):
    if sth is not None:
        sth.waitForCompletion(-1)

class Kylin:
    mgr=vboxapi.VirtualBoxManager()
    vbox=mgr.vbox
    vm=vbox.findMachine(const.VM_NAME)

    def __init__(self,log):
        self.log=log
        self.log('=== initializing')
        self.session=self.mgr.getSessionObject(self.vbox)

    def _boot(self):
        self.vm=self.vbox.findMachine(const.VM_NAME)
        self.session=self.mgr.getSessionObject(self.vbox)
        self.log('=== launching')
        while True:
            try:
                wait(self.vm.launchVMProcess(self.session,'gui' if const.DEBUG else 'headless',''))
            except pywintypes.com_error: #still unlocking machine
                time.sleep(.1)
            else:
                break
        self.log('=== waiting for gs')
        while True:
            try:
                result=self._execute('judge',const.VM_JUDGE_PSW,'/bin/echo',['hello','world'],1000)
                assert result[0]==0 and result[1].startswith('hello world') and not result[2]
            except (AssertionError,pywintypes.com_error):
                time.sleep(.1)
            else:
                break

    def _execute(self,user,passwd,program,args,timeout=15000,stdin=None):
        def read_out():
            process.waitFor(7,0)
            o=process.read(1,65000,0).tobytes().decode('utf-8','ignore')
            stdout.append(o)
            process.waitFor(8,0)
            e=process.read(2,65000,0).tobytes().decode('utf-8','ignore')
            stderr.append(e)

        if self.session.state==1:
            self.session=self.mgr.openMachineSession(self.vm)

        self.log('=== creating process')
        with closing(self.session.console.guest.createSession(user,passwd,"","kylinOJ execute session")) as gs:
            while gs.status!=100:
                time.sleep(.02)
            process=gs.processCreate(program,[program]+args,[],[16,32],timeout)
            process.waitFor(1,0)

            if stdin:
                self.log('=== writing stdin')
                process.waitFor(4,0)
                index=0
                while index<len(stdin):
                    array=map(lambda a:str(ord(a)),stdin[index:])
                    wrote=process.writeArray(0,[0],array,0)
                    if not wrote:
                        if process.status<=100:
                            raise RuntimeError('Failed to write ANY bytes to STDIN')
                        else: #terminated
                            break
                    index+=wrote
                process.writeArray(0,[1],[],0)

            self.log('=== executing')
            stdout,stderr=[],[]
            while process.status<=100:
                read_out()
                time.sleep(0.02)
            self.log('=== stopped')
            read_out()

            return process.exitCode,''.join(stdout),''.join(stderr)

    def _writefile(self,user,passwd,filename,content):
        if self.session.state==1:
            self.session=self.mgr.openMachineSession(self.vm)

        self.log('=== initializing gs')
        with closing(self.session.console.guest.createSession(user,passwd,"","kylinOJ writefile session")) as gs:
            while gs.status!=100:
                time.sleep(.02)
            self.log('=== writing')
            with closing(gs.fileOpen(filename,2,4,0x755)) as handler:
                handler.write(content.encode('utf-8','ignore'),1000)

    def pwn(self):
        self.log('=== writing judger')
        with open('vm_files/judger.cpp','r') as f:
            self._writefile('root',const.VM_ROOT_PSW,'/root/judger.cpp',f.read())

        self.log('=== compiling judger')
        errcode,out,err=self._execute('root',const.VM_ROOT_PSW,'/usr/bin/g++',['-static','-o','/root/judger','/root/judger.cpp'])
        if errcode:
            self.log('!!! errcode = %d'%errcode)
            self.log('[STDOUT]\n%s\n[STDERR]\n%s'%(out,err))

    def restore(self):
        if self.session.state!=1:
            self.log('=== powering down')
            wait(self.session.console.powerDown())
            wait(self.session.unlockMachine())

        self.log('=== opening session')
        self.session=self.mgr.openMachineSession(self.vm)
        self.vm=self.session.machine
        self.log('=== restoring')
        wait(self.vm.restoreSnapshot(self.vm.findSnapshot(const.VM_BASE_SNAPSHOT)))
        wait(self.session.unlockMachine())

        self._boot()

if __name__=='__main__':
    kylin=Kylin(print)
    #kylin.restore()
    #kylin.pwn()
    #xx=kylin._execute('root',const.VM_ROOT_PSW,'/home/judge/program',[],3000)
    #xx=kylin._writefile('root',const.VM_ROOT_PSW,'/root/foo.bar','hello world!')
