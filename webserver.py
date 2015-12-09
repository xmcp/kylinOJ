#coding=utf-8
import const
import kylin

import os
import cherrypy
from mako.lookup import TemplateLookup
import sqlite3
import math
import markdown
lookup_=TemplateLookup(directories=['templates'],input_encoding='utf-8',output_encoding='utf-8')
def lookup(name):
    class _sub:
        @staticmethod
        def render(**_):
            return lookup_.get_template(name).render(
                session=cherrypy.session, uri=cherrypy.request.path_info, **_
            )
    return _sub

def err(e):
    return lookup('err.html').render(e=e)

class Website:
    @cherrypy.expose()
    def index(self):
        return lookup('index.html').render()

    @cherrypy.expose()
    def problem(self,problemid=None,page=1):
        page=int(page)
        db=sqlite3.connect(const.DBFILE)
        cur=db.cursor()
        if problemid is None:
            cur.execute('select count(*) from problems')
            count,*_=cur.fetchone()
            pages=math.ceil(count/50)
            if page>pages or page<=0:
                return err('页码范围错误')

            cur.execute('select id,title,subtitle,acuser,alluser from problems order by id asc limit ?,50',[(page-1)*50])
            result=[]
            for problemid,title,subtitle,acuser,alluser in cur.fetchall():
                result.append({'id':problemid,'title':title,'subtitle':subtitle,'acuser':acuser,'alluser':alluser})
            return lookup('problem_list.html').render(problems=result,curpage=page,pages=pages)
        else:
            cur.execute('select title,subtitle,acuser,alluser,description,memory,time from problems where id=?',[problemid])
            title,subtitle,acuser,alluser,description,memory,allowtime=cur.fetchone()
            html=markdown.markdown(description,output_format='html5',lazy_ol=False)
            return lookup('problem.html').render(probtitle=title,subtitle=subtitle,acuser=acuser,alluser=alluser,\
                description=html,memory=memory,time=allowtime)


cherrypy.quickstart(Website(),'/',{
    'global': {
        'engine.autoreload.on':False,
        #'request.show_tracebacks': False,
        'server.socket_host':'0.0.0.0',
        'server.socket_port':1243,
    },
    '/': {
        'tools.gzip.on': True,
        'tools.sessions.on': True,
    },
    '/static': {
        'tools.staticdir.on':True,
        'tools.staticdir.dir':os.path.join(os.getcwd(),'static'),
    },
})