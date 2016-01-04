# -*- coding: utf-8 -*-
'''
Created on Dec 19, 2015

@author: Roman Ost.
'''

import os
import platform
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
from bs4 import BeautifulSoup
from torrent2http import State, Engine, MediaType, Error
import requests
from contextlib import closing


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
site_url="http://tv-torrent.org"
srch_url=site_url+"/index.php?do=search&subaction=search"  ## +page+string
faddon=xbmcaddon.Addon(id='plugin.video.tv-torrent')
#temp_dir="/storage/.kodi/temp/torrent2http/"
temp_dir=xbmc.translatePath(os.path.join("special://temp","torrent2http"))

xbmcplugin.setContent(addon_handle, 'movies')
items=[]
#if not os.path.exists(temp_dir):
if not os.path.isdir(temp_dir):
    os.makedirs(temp_dir)

def log(s,lvl="NOTICE"):
    output="[plugin.video.tv-torrent]: "+s
    print output

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def get_site(s_url):
    return urllib2.urlopen(s_url).read()

def endoflist():
    #log("Adding items")
    xbmcplugin.addDirectoryItems(addon_handle, items, len(items))
    #xbmcplugin.addSortMethod(addon_handle,xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)
    return

def parse(link):
    #log("Parsing")
    page=get_site(link)
    return BeautifulSoup(page)

def parse_page(page,h="h2"):
    b=page.body.findAll("div", {"class":"dpad"})
    
    ## find name and link
    for b1 in b[3:]:
        try: 
            sinfo={}
            s=b1.find(h).find("a").string
            l=b1.find(h).find("a")['href']
        
            s=s.replace(u"Скачать торрент", "")
            s=s.strip()
            sname=s
            
            ## find quality
            k=b1.find("span",{"class":'kachestvooo'})
            if k:
                k=k.string.strip()
            else:
                k=""
            sinfo['title']=sname+" | "+k
            
            ## find genres
            b2=b1.find("p",{'class':"argcat small"}).find_all("a")
            g=""
            for b3 in b2:
                g=g+b3.string+","
            g=g[:-1]
            sinfo['genre']=g
            ## find img
            b2=b1.find("img")
            i=site_url+b2['src']
            
            ## info
            b2=b1.find("div",{'class':'maincont'}).find("i").text.strip()
            sinfo['plot']=b2
            
            url=build_url({'mode':'series', 'slink':l})
            add_link(url,sname,True,simg=i,sinfo=sinfo)
        except:
            pass

def add_link(s_url,sname,isfldr=False,simg='DefaultFolder.png',contx=[],sinfo={}):
    #log("adding:"+sname)
    li = xbmcgui.ListItem(sname, iconImage=simg)
    if sinfo:
        li.setInfo('video',sinfo)
    if not isfldr:
        li.setProperty('IsPlayable','true')
    if contx:
        li.addContextMenuItems(contx)
    items.append((s_url,li,isfldr))
    return True

def get_tor(surl,refer=""):
    head={"Referer": "http://tv-torrent.org/"}
    rrr=requests.Session()
    req=requests.Request('GET',surl,headers=head)
    z=req.prepare()
    resp=rrr.send(z)
    #fname="/tmp/"+
    fname=os.path.join(temp_dir,resp.headers['Content-Disposition'].split('"')[-2])
    with open(fname,'wb') as f:
        f.write(resp.content)
    return fname

def get_files(t_url):
    engine = Engine(uri=t_url,download_path=temp_dir,bind_host='127.0.0.1',bind_port=5001)
    file_id = None
    files=[]
    try:
        with closing(engine):
            engine.start(0)
            files = engine.list(media_types=[MediaType.VIDEO])
            n=files[0].name
    except Error as err:
        print "Error"
        print err
    return files
    
mode = args.get('mode', None)

#print sys.argv 

if mode is None:
    url = build_url({'mode': 'search'})
    add_link(url,'Search',True)
    url = build_url({'mode': 'browse'})
    add_link(url,'Browse by pages',True)
    url = build_url({'mode': 'genres'})
    add_link(url,'Browse by genres',True)
    url = build_url({'mode': 'customfile'})
    add_link(url,'Open torrent file',True)
    url = build_url({'mode': 'customurl'})
    add_link(url,'Open torrent URL',True)
    endoflist()

elif mode[0] == 'search': 
    if 'slink' in args:
        slink=args['slink'][0]
        ksrch=args['sstory'][0]
    else:
        slink=""
        kkbd=xbmc.Keyboard("", "Search for:",False)
        kkbd.doModal()
        if (kkbd.isConfirmed()):
            ktext=unicode(kkbd.getText(),"utf-8")
            ktext=ktext.encode('utf-8')
            ksrch=urllib.quote_plus(ktext)
            slink=srch_url+"&search_start=1&story="+ksrch
    if slink:        
        page=parse(slink)
        parse_page(page,"h3")
        try:    
            b1=page.body.find("div",{"class":"nextprev"}).find_all("a")
            for b2 in b1:
                s=str(b2['onclick'])
                i=filter(str.isdigit,s)
                slink=srch_url+"&search_start="+str(i)+"&story="+ksrch
                url=build_url({'mode':'search', 'slink':slink,'sstory':ksrch})
                add_link(url,b2.string,True)
        except:
            pass
        
        endoflist()

elif mode[0] == 'browse':
    if 'slink' in args:
        slink=args['slink'][0] 
    else:
        slink=site_url
    #log("Start browse")
    page=parse(slink)
    parse_page(page)
    try:    
        b1=page.body.find("div",{"class":"nextprev"}).find_all("a")
        for b2 in b1:
            url=build_url({'mode':'browse', 'slink':b2['href']})
            add_link(url,b2.string,True)
    except:
        pass
    
    endoflist()    


elif mode[0] == 'genres':
    page=parse(site_url)
    b1=page.body.findAll("div", {"class":"block leftmenu"})
    b2=b1[0].find_all("li")
    for b in b2:
        b3=b.find_all("a")
        if b3[0]['href'][:4]=="http":
            url=build_url({'mode':'browse', 'slink':b3[0]['href']})
            add_link(url,b3[0].string,True)
    endoflist()    

elif mode[0] == 'series':
    slink=args['slink'][0]
    page=parse(slink)
    #print "Series"
    b1=page.findAll("span", {"class":"yad"})
    for b2 in b1:
        b3=b2.find_all("a")
        n=b3[0].string.strip()
        t=b3[0]['href']
        url=build_url({'mode':'customurl', 'slink':b3[0]['href']})
        add_link(url,b3[0].string,True)
    endoflist()    

elif mode[0] == 'customfile':
    xfile=xbmcgui.Dialog()
    selfile=xfile.browseSingle(1,'Choose file','files','*.torrent')
    if selfile:
        if platform.uname()[0]=="Linux":
            selfile="file://"+selfile
        else:
            selfile="file:/"+selfile
            selfile=selfile.replace("\\","\/")                                                          
        t=get_files(selfile)
        for f in t:
            url=build_url({'mode':'playtorrent', 'sname':f.name, 'sid':f.index, 'slink':selfile})
            add_link(url,f.name)
        endoflist()    
    else:
        print "no file selected"
    
elif mode[0] == 'customurl':
    if 'slink' in args:
        slink=args['slink'][0]
        ref="http://tv-torrent.org/" 
    else:
        ref=""
        xfile=xbmcgui.Dialog()
        slink=xfile.input("Enter torrent URL")
    if slink:
        if platform.uname()[0]=="Linux":
            selfile="file://"+get_tor(slink,ref)
        else:
            selfile="file:/"+get_tor(slink,ref)
            selfile=selfile.replace("\\","\/")                                                          
        #selfile="file://"+get_tor(slink,ref)
        t=get_files(selfile)
        for f in t:
            url=build_url({'mode':'playtorrent', 'sname':f.name, 'sid':f.index, 'slink':selfile})
            add_link(url,f.name)
        endoflist()    
    else:
        print "no url entered"

elif mode[0] == 'playtorrent':
    surl=args['slink'][0]
    sname=args['sname'][0]
    sid=int(args['sid'][0])
    ready = False
    pre_buffer_bytes = 15*1024*1024
    engine = Engine(uri=surl,download_path=temp_dir,bind_host='127.0.0.1',bind_port=5001)
     
    progress = xbmcgui.DialogProgress()
    progress.create('Downloading', 'Prebuffering...')
    
    try:
        with closing(engine):
            engine.start(sid)
            #xbmcgui.DialogProgress()
            while not xbmc.abortRequested and not ready and not progress.iscanceled():
                xbmc.sleep(500)
                status = engine.status()
                print "Status:",status
                engine.check_torrent_error(status)
                files = engine.list(media_types=[MediaType.VIDEO])
                file_status = engine.file_status(sid)
                if status.state == State.DOWNLOADING:
                    prcnt=100.0
                    prcnt=prcnt*file_status.download/pre_buffer_bytes
                    s1="Downloaded: "+str(file_status.download/1024/1024)+"MB of 15MB"
                    s2="D: "+str(int(status.download_rate))+"KB/s U: "+str(int(status.upload_rate))+"KB/s"
                    s3="Peers: "+str(status.num_peers)+" Seeds: "+str(status.num_seeds)
                    progress.update(int(prcnt),s1,s2,s3)
                    if file_status.download >= pre_buffer_bytes:
                        ready = True
                        break
                elif status.state in [State.FINISHED, State.SEEDING]:
                    ready = True
                    break
            if ready:
#                 i=int(status.progress*100.0)
#                 s1=status.state_str+" / "+str(i)+"\n"
#                 s2="D: "+str(int(status.download_rate))+"KB/s U: "+str(int(status.upload_rate))+"KB/s\n"
#                 s3="Peers: "+str(status.num_peers)+" Seeds: "+str(status.num_seeds)+"\n"
                 
                u=file_status.url
                li=xbmcgui.ListItem()
                li.setPath(u)
                xbmcplugin.setResolvedUrl(addon_handle, True, li)
                progress.close()
                xbmc.sleep(3)
                while not xbmc.abortRequested and xbmc.Player().isPlaying():
                    xbmc.sleep(500)

    except Error as err:
        print err
    #progress.close() 
    #pprogress.close()

else:
    
    log("Error!!! unknown mode:")
    log(mode[0])
        
    
      
