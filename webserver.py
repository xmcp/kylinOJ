#coding=utf-8
import const
import kylin

import os
import cherrypy
from mako.lookup import TemplateLookup
import sqlite3
import hashlib
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

def post_only():
    if cherrypy.request.method.upper()!='POST':
        cherrypy.response.headers['Allow']='POST'
        raise cherrypy.HTTPError(405)
cherrypy.tools.post=cherrypy.Tool('on_start_resource',post_only)

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
            pages=math.ceil(count/20)
            if page>pages or page<=0:
                return err('页码范围不正确')

            cur.execute('select id,title,subtitle,acuser,alluser from problems order by id asc limit ?,20',[(page-1)*20])
            result=[]
            for problemid,title,subtitle,acuser,alluser in cur.fetchall():
                result.append({'id':problemid,'title':title,'subtitle':subtitle,'acuser':acuser,'alluser':alluser})
            return lookup('problem_list.html').render(problems=result,curpage=page,pages=pages)
        else:
            cur.execute('select title,subtitle,acuser,alluser,description,memory,time from problems where id=?',[problemid])
            result=cur.fetchone()
            if result:
                title,subtitle,acuser,alluser,description,memory,allowtime=result
                html=markdown.markdown(description,output_format='html5',lazy_ol=False)
                return lookup('problem.html').render(probtitle=title,subtitle=subtitle,acuser=acuser,alluser=alluser,
                    description=html,memory=memory,time=allowtime,id_=problemid)
            else:
                raise cherrypy.NotFound()

    @cherrypy.expose()
    def login(self,username=None,password=None):
        ha=lambda u,p: hashlib.sha384(('U "%s" --> P "%s"'%(u,p)).encode()).hexdigest()

        if 'username' in cherrypy.session:
            raise cherrypy.HTTPRedirect('/')
        if not username:
            return lookup('login.html').render()
        elif not password:
            db=sqlite3.connect(const.DBFILE)
            cur=db.cursor()
            cur.execute('select exists(select * from users where username=?)',[username])
            return 'login' if cur.fetchone()[0] else 'register'
        else:
            db=sqlite3.connect(const.DBFILE)
            cur=db.cursor()
            cur.execute('select password from users where username=?',[username])
            result=cur.fetchone()
            if result: #login
                if ha(username,password)==result[0]:
                    cherrypy.session['username']=username
                    raise cherrypy.HTTPRedirect('/')
                else:
                    return err('密码不正确')
            else: #signup
                cur.execute('insert into users values ()',[username,ha(username,password)])
                db.commit()
                cherrypy.session['username']=username
                raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    @cherrypy.tools.post()
    def logout(self):
        if 'username' in cherrypy.session:
            del cherrypy.session['username']
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    @cherrypy.tools.post()
    def submit(self,problemid,code):
        if 'username' not in cherrypy.session:
            raise cherrypy.HTTPRedirect('/login')
        return code #todo


cherrypy.quickstart(Website(),'/',{
    'global': {
        'engine.autoreload.on':False,
        #'request.show_tracebacks': False,
        'server.socket_host':'0.0.0.0',
        'server.socket_port':1243,
        'error_page.404': lambda status,message,traceback,version:err(status),
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