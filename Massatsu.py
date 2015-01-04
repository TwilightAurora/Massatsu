import urllib
import urllib2
import re
import cookielib
import json
import os
from bs4 import BeautifulSoup

cookie = cookielib.CookieJar()
cookie_support = urllib2.HTTPCookieProcessor(cookie)
opener = urllib2.build_opener(cookie_support)
urllib2.install_opener(opener)
#init
def login():
    global requestToken
    global _rtk
    request = urllib2.Request("http://www.renren.com/PLogin.do",urllib.urlencode(params))
    opener.open(request)
    response = opener.open('http://www.renren.com')
    text=response.read()

    requestToken=re.search(r"get_check:'[-,\d]+'",text).group(0)[11:-1]
    _rtk=re.search(r"get_check_x:'\w+'",text).group(0)[13:-1]


    #get personal ID
    global UID
    UID = re.search('\d+',response.geturl()).group(0)
    print 'UID='+UID, 'requestToken='+requestToken, '_rtk='+_rtk


#albums
#Download a photo
def DownloadPhoto(photoid,owner,ab):
    owner=UID
    turl='http://photo.renren.com/photo/'+str(UID)+'/photo-%s/' %(photoid)
    text=opener.open(urllib2.Request(turl)).read()
    temp=re.search(r'<img id="photo" src="\S+" title="" />',text).group(0)
    photourl=re.search(r'http://\S+.jpg',temp).group(0)
    filename=str(photoid)
    album_dir=os.path.join(ab,str(photoid))
    if not os.path.isdir(album_dir): os.mkdir(album_dir)
    f=file(os.path.join(album_dir,str(photoid)+'.jpg'),'wb')
    f.write(opener.open(urllib2.Request(photourl)).read())
    f.close()

    #GetDiscription&time
    f=file(os.path.join(album_dir,'discription.txt'),'w')
    temp=re.search(r' originTitle="[\s\S]*" data-wiki',text).group(0)
    discription=temp[14:-11]
    f.write('Discription='+discription+'\n')
    temp=re.search(r'<span id="update_time">\S+</span>',text).group(0)
    uploadtime=temp[23:-7]
    f.write('UploadTime='+uploadtime+'\n')
    temp=re.search(r'<span id="commentCount">\d+</span>',text).group(0)
    commentCount=temp[24:-7]
    
    f.write('CommentCount='+commentCount+'\n')
    temp=re.search(r'<span id="viewCount">\d+</span>',text).group(0)
    viewCount=temp[21:-7]
    f.write('ViewCount='+viewCount+'\n')
    try:
        temp=re.search(r'photoNum":\d+,"currentPhoto":{"position":\d+,',text).group(0)
        photoNum=temp[10:temp.find(',')]
        position=temp[temp.rfind(':')+1:-1]
        f.write(position+'/'+photoNum)
    except:
        f.write('Failed to get position and photoNum')
    
    f.close()

    #GetComment
    fp = open(os.path.join(album_dir,"comment.txt"),'w')
    flag=True
    count=0
    while flag:
        turl='http://photo.renren.com/photo/'+str(UID)+'/photo-%s/comment?page=%s&photo=%s&owner=%s&ref=singlephoto' %(photoid,count,photoid,owner)
        response=opener.open(urllib2.Request(turl))
        text=response.read()
        a=json.loads(text)
        flag=a['hasMore']
        count=count+1
        for s in a['comments']:
            fp.write(s['name'].encode('utf-8')+'\t')
            fp.write(s['body'].encode('utf-8')+'\n')
            fp.write(s['time'].encode('utf-8')+'\t')
            fp.write('likes:'+str(s['likecount'])+'\t')
            fp.write('whisper?'+str(s['whisper']).encode('utf-8')+'\n')
    fp.close()



#Get Photos in an album and download
def GetAlbumPhoto(albumid,owner):
    #get total photo number & pages
    turl='http://photo.renren.com/photo/'+str(UID)+'/album-%s' %albumid
    text=opener.open(urllib2.Request(turl)).read()
    temp=re.search(r'<span class="num">(\S+)</span></h1>',text).group(0)
    number=int(re.search(r'\D\d+\D',temp).group(0)[1:-1])
    pages=(number-1)/20+1
    print 'Total Number & Pages:' + str(number)+' '+str(pages)
    
    #get album name
    temp=re.search(r'<title>.+</title>',text).group(0).decode('utf-8')
    albumname=temp[20:-8]
    print albumname
    
    #make dir
    currentAlbumDir=os.path.join('albums',albumname)
    currentAlbumDir=re.sub(r'[:\/*?.]','_',currentAlbumDir) #if name is not legal filename
    if not os.path.isdir(currentAlbumDir): os.mkdir(currentAlbumDir)

    #GetComment
    fp=open(os.path.join(currentAlbumDir,"comment.txt"),'w')
    flag=True
    count=0
    while flag:
        turl='http://photo.renren.com/photo/'+str(UID)+'/album-%s/comment?page=%s&album=%s&owner=%s' %(albumid,count,albumid,UID)
        text=opener.open(urllib2.Request(turl)).read()
        a=json.loads(text)
        flag=a['hasMore']
        count=count+1
        for s in a['comments']:
            fp.write(s['name'].encode('utf-8')+'\t')
            fp.write(s['body'].encode('utf-8')+'\n')
            fp.write(s['time'].encode('utf-8')+'\t')
            fp.write('likes:'+str(s['likecount'])+'\t')
            fp.write('whisper?'+str(s['whisper']).encode('utf-8')+'\n')        
    fp.close()
    print 'Get Comments'
    
    #get photoid in this album
    l=[] #list of photoid
    
    for p in range(0,number+1):
        turl='http://photo.renren.com/photo/'+str(UID)+'/album-%s/bypage/ajax?curPage=%s&pagenum=1' %(albumid,p)
        text=opener.open(urllib2.Request(turl)).read()
        temp=re.findall(r'"photoId":"\d+"',text)
        for s in temp:
            l.append(s[11:-1])
    for s in l:
        if not os.path.isfile(os.path.join(currentAlbumDir,s,s+'.jpg')):
            print 'Downloading Photo '+str(s)
            DownloadPhoto(s,UID,currentAlbumDir)
        else:
            print 'Ignored Photo '+str(s)

#GetAlbumList
def GetAlbumList(owner):
    if not os.path.isdir('albums'): os.mkdir('albums')
    turl='http://photo.renren.com/photo/%s?__view=async-html' %owner
    text=opener.open(urllib2.Request(turl)).read()
    temp=re.findall(r'<a href=".+" class="album-title">',text)
    l=[]
    #read log file to get ignore list
    try:
        f=open('AlbumLog.txt','r')
        text=f.read()
        l=text.split('\n')
        f.close()
    except:
        print 'No Log File'
    #write new log file    
    f=open('AlbumLog.txt','w')
    for s in temp:
        temp2=re.search(r'-\d+"',s).group(0)[1:-1]
        
        if temp2 in l:
            print 'Ignored Album: '+temp2
        else:
            print 'Processing Album id '+temp2
            GetAlbumPhoto(temp2,owner)
        f.write(temp2+'\n')
    f.close()
    pass


#Blog

def DownloadBlog(blogid,owner,bpath):
    if not os.path.isdir(os.path.join(bpath,blogid)): os.mkdir(os.path.join(bpath,blogid))
    bpath=os.path.join(bpath,blogid)
    turl='http://blog.renren.com/blog/%s/%s' %(owner,blogid)
    text=opener.open(urllib2.Request(turl)).read()
    #download article
    soup=BeautifulSoup(text)
    a=soup.find('div',{'class':'text-article'}).findParent()
    useless=a.findAll('a')
    [x.extract() for x in useless]
    fp=open(os.path.join(bpath,'%s.htm' %blogid),'wb')
    fp.write(str(a))
    fp.close()
    #get comments
    fp=open(os.path.join(bpath,'comments.txt'),'w')
    start=text.find('Blog.init')
    end=text.find('Blog.editor = new XN.ui.emoticons')
    substart=text[start+10:end-2].find('comments')
    newtext='{'+text[start+10:end-4][substart+10:]
    #print newtext
    a=json.loads(newtext)
    hasMore=a['hasMore']
    commentCount=a['commentCount']
    fp.write('CommentCount: '+str(commentCount)+'\n')
    a['comments'].reverse()
    for s in a['comments']:
        body=s['body']
        name=s['name']
        time=s['time']
        likeCount=s['likeCount']
        lastComment=s['id']
        fp.write(name.encode('utf-8')+' '+body.encode('utf-8')+'\n')
        fp.write(time.encode('utf-8')+' '+'LikeCount: '+str(likeCount)+'\n')
    while hasMore:
        lastComment=str(int(lastComment))
        print lastComment
        turl='http://blog.renren.com/blog/%s/%s/comment/list/by-%s' %(owner,blogid,lastComment)
        text=opener.open(urllib2.Request(turl)).read()
        a=json.loads(text)
        hasMore=a['hasMore']
        commentCount=a['commentCount']
        fp.write('CommentCount: '+str(commentCount)+'\n')
        a['comments'].reverse()
        for s in a['comments']:
            body=s['body']
            name=s['name']
            time=s['time']
            likeCount=s['likeCount']
            lastComment=s['id']
            fp.write(name.encode('utf-8')+' '+body.encode('utf-8')+'\n')
            fp.write(time.encode('utf-8')+' '+'LikeCount: '+str(likeCount)+'\n')
        
    fp.close()

def GetBlogList(owner):
    if not os.path.isdir('Blog'): os.mkdir('blogs')
    turl='http://blog.renren.com/blog/%s?__view=async-html' %owner
    text=opener.open(urllib2.Request(turl)).read().decode('utf-8')
    #total number and pages of blogs
    total=int(re.search(u'\u5171\d+\u7bc7',text).group(0)[1:-1])
    pages=(total-1)/10+1
    for p in range(0,pages):
        turl='http://blog.renren.com/blog/%s?curpage=%s&__view=async-html'%(owner,p)
        text=opener.open(urllib2.Request(turl)).read()
        a=re.findall(r'<a href="javascript:;" class="multiwork-more" blogId="\d+">',text)
        for s in a:
            temp=re.search(r'"\d+"',s).group(0)[1:-1]
            print temp
            DownloadBlog(temp,owner,'blogs')
        
    
    
    

    
#Status

def GetStatus(owner):
    if not os.path.isdir('Status'): os.mkdir('Status')
    curPage=0
    totalPage=1
    errorlist=[]
    while curPage<=totalPage:
        turl='http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%s' %(owner,curPage)
        text=opener.open(urllib2.Request(turl)).read()
        a=json.loads(text)
        #total status
        total=int(a['count'])
        totalPage=(total-1)/20+1
        b=a['doingArray']
        for s in b:
            commentCount=s['comment_count']
            time=s['dtime']
            content=s['content'].encode('utf-8')
            repeatCount=s['repeatCount']
            sid=int(s['id'])
            print sid
            if os.path.isfile(os.path.join('Status',str(sid))+'.txt'):
                print 'Ignored '+str(sid)
                continue
            fp=open(os.path.join('Status',str(sid))+'.txt','w')
            #print content
            fp.write(content+'\n')
            fp.write(time+'\n')
            fp.write('RepeatCount: '+str(repeatCount)+'\n')
            fp.write('CommentCount: '+str(commentCount)+'\n')
            fp.write('Comments:\n')
            #Get Comment
            
            turl='http://status.renren.com/feedcommentretrieve.do?doingId=%s&source=%s&owner=%s&t=3' %(sid,sid,owner)
            text=opener.open(urllib2.Request(turl)).read()
            aab=json.loads(text)
            try:
                aa=aab['replyList']
            except:
                errorlist.append(sid)
                fp.close()
                os.remove(os.path.join('Status',str(sid))+'.txt')
                continue
            for ss in aa:
                likeCount=ss['likeCount']
                name=ss['ubname'].encode('utf-8')
                replyTime=ss['replyTime']
                replyContent=ss['replyContent'].encode('utf-8')
                fp.write(name+'\t'+str(replyContent)+'\n')
                fp.write(replyTime+'\n')
                fp.write('likeCount: '+str(likeCount)+'\n')
            fp.close()
        curPage=curPage+1
    print errorlist
    if len(errorlist)>0:
        print "Rework"
        GetStatus(owner)
        #print 'Plz Run GetStatus Once More (maybe more times..)'
        #print 'too lazy to improve'
        
def GetStatusList(owner):
    curPage=0
    totalPage=1
    deleteList=[]
    while curPage<=totalPage:
        turl='http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%s' %(owner,curPage)
        text=opener.open(urllib2.Request(turl)).read()
        a=json.loads(text)
        #total status
        total=int(a['count'])
        totalPage=(total-1)/20+1
        b=a['doingArray']
        for s in b:
            sid=int(s['id'])
            deleteList.append(sid)
            print sid
        curPage=curPage+1
    #print len(deleteList)
    return deleteList

def DeleteList(l):
    for s in l:
        turl='http://status.renren.com/doing/deleteDoing.do'
        postData=urllib.urlencode({'id':s,'owner':UID,'requestToken':requestToken,'_rtk':_rtk})
        print postData
        text=opener.open(turl,postData).read()
        print text
        try:
            a=json.loads(text)
            print 'Success '+str(s)
        except:
            print 'Not Successful ' + str(s)

#Messages
def DownloadMessage(mid,owner):
    turl='http://gossip.renren.com/ajaxgossiplist.do'
    p=0
    fp=open('Messages.txt','w')
    postData=urllib.urlencode({
        'guest':owner,
        'page':p,
        'id':owner,
        'requestToken':requestToken,
        '_rtk':_rtk})
    text=opener.open(turl,postData).read()
    a=json.loads(text)
    total=a['gossipCount']
    pages=(total-1)/20+1

    while p<pages+1:
        print 'page'+str(p)
        postData=urllib.urlencode({
            'guest':owner,
            'page':p,
            'id':owner,
            'requestToken':requestToken,
            '_rtk':_rtk})
        text=opener.open(turl,postData).read()
        a=json.loads(text)
        for s in a['array']:
            l.append(s['id'])
            fp.write(s['guestName'].encode('utf-8')+' ')
            fp.write(s['filterOriginalBody'].encode('utf-8')+'\n')
            fp.write(s['time'].encode('utf-8')+' ')
            if s['whisper']:
                fp.write('Whisper')
            else:
                fp.write('Public ')
            if s['wap']=='true':
                fp.write(' WAP')
            fp.write('\n')
        p=p+1
    print 'total messages: '+str(len(l))
    fp.close()
    
def DeleteMessages(deletelist,owner):
    turl='http://gossip.renren.com/delgossip.do'
    for s in deletelist:
        postData=urllib.urlencode({
            'id':s,
            'owner':owner,
            'requestToken':requestToken,
            '_rtk':_rtk})
        text=opener.open(turl,postData).read()
        print s+' '+text





#Manual
#Status:
#l=[]
#l=GetStatusList(UID)
#DeleteList(l)
#GetStatus(UID)

#Album:
#GetAlbumList(UID)                   
        
#Blog:
#GetBlogList(UID)    

#Message:
#l=[]
#DownloadMessage(0,UID)
##DeleteMessages(l,UID)

def info():
    print "\t\tRENREN MASSATSU"
    print "\tSKY EXTINCT PEOPLE PEOPLE WEB"
    print "\tEXIT  WEB REMAIN FLAT  SAFETY"
    print "Input 1 to backup Status (to \\status folder)."
    print "Input 2 to backup Albums (to \\albums folder)."
    print "Input 3 to backup Blogs  (to \\blogs  folder)."
    print "Input 4 to backup all message (to Messages.txt)."
    print "Input anything I do not understand to exit."
if __name__=="__main__":
    global params
    params={}
    print "\t\tRENREN MASSATSU"
    print "\tSKY EXTINCT PEOPLE PEOPLE WEB"
    print "\tEXIT  WEB REMAIN FLAT  SAFETY"
    print "Please input your account and password(hopefully would not be uploaded)."
    params['email']= raw_input("Account:")
    params['password']=raw_input("Password:")
    login()
    print " "
    print "Input 1 to backup Status (to \\status folder)."
    print "Input 2 to backup Albums (to \\albums folder)."
    print "Input 3 to backup Blogs  (to \\blogs  folder)."
    print "Input 4 to backup all message (to Messages.txt)."
    print "Input anything I do not understand to exit."
    ch=raw_input("Thy bidding, master?")
    while ch in {'1','2','3','4'}:
        l=[]
        if ch == '1':
            GetStatus(UID)
        if ch == '2':
            GetAlbumList(UID)
        if ch == '3':
            GetBlogList(UID)
        if ch == '4':
            DownloadMessage(0,UID)
        print ' '
        print '------FINISHED------'
        print ' '
        
        info()
        ch=raw_input("Thy bidding, master?")
