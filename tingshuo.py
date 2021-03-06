#!/usr/bin/env python  
import tornado.ioloop
import tornado.web
import MySQLdb
import hashlib
import json
import sys
import ConfigParser
import threading
import time
import datetime
import signal
import string,os
from time import ctime,sleep
reload(sys)
sys.setdefaultencoding('utf-8')

#define skill type
SKILLTYPE = {
	'addlike': 	0,
	'addgold': 	1,
	'addtime': 	2,
	'addlikenormal':3,
	'dellike': 	4,
	'momoda':	5,
	'yun':		6,
	'bukaixin':	7,
	'youqianren':	8,
	'weixiao':	9,
	'lengmo':	10,
	'doge':		11,
	'guilian':	12,
	'aixinyan':	13,
	'guale':	14
}

def db_init():
	cf = ConfigParser.ConfigParser()
	cf.read("db.conf")

	secs = cf.sections()
	print 'sections:', secs

	opts = cf.options("db")
	print 'options:', opts
	  
	kvs = cf.items("db")
	print 'db:', kvs

	#read by type
	global DB_HOST 
	global DB_NAME 
	global DB_USER 
	global DB_PASSWD
	DB_HOST = cf.get("db", "db_host")
	DB_NAME = cf.get("db", "db_name")
	DB_USER = cf.get("db", "db_user")
	DB_PASSWD = cf.get("db", "db_pass")

	print DB_HOST, DB_NAME, DB_USER, DB_PASSWD


def get_user_id(acc):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "select id, nickname from member where account=\'" + acc + "\'";
		result = cur.execute(sql);
		uid = 0;
		for id, nickname in cur.fetchall():
			print id, nickname, '\n';
			uid = id;
		conn.commit();
		cur.close();
		conn.close();
		return uid;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_user_acc(uid):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "select account, nickname from member where id=" + uid;
		print sql, "\n";
		result = cur.execute(sql);
		acc = "";
		for account, nickname in cur.fetchall():
			acc = account;
		conn.commit();
		cur.close();
		conn.close();
		return acc;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def get_user_read_msg_id(acc):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "select id, readmsgno from member where account=\'" + acc + "\'";
		result = cur.execute(sql);
		msgno = 0;
		for id, readmsgno in cur.fetchall():
			msgno = readmsgno;
		conn.commit();
		cur.close();
		conn.close();
		return msgno;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def add_like(msgid):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql1 = "update message set likecnt = likecnt + 1 where id="+msgid;
		cur.execute(sql1);
		sql2 = "update member  set gold = gold + 2 , totallike = totallike +1 , todaylike = todaylike +1 where id = (select uid from message where id=" +msgid + ")";
		cur.execute(sql2);
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def add_gold(uid, num):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		u=uid
		n=num
		sqll = "update member set gold = gold+" + str(n) + " where id=" + str(u);
		#print sqll;
		cur.execute(sqll);
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def del_gold(uid, num):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "update member set gold = gold-" + str(num) + " where id=" + str(uid) + " and gold >= " + str(num);
		result = cur.execute(sql);
		conn.commit();
		cur.close();
		conn.close();
		if result == 1:
			return 1;
		else:
			return 0;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def del_msg(uid, msgid):
	try:
		conn = getDBConn('''tingshuo''');
		conn.select_db('tingshuo');
		cur = conn.cursor()
		sql = "delete from message where id=" + str(msgid) + " and uid=" + str(uid);
		cur.execute(sql);
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_msg(msgid, msgs):
	try:
		conn = getDBConn('''tingshuo''');
		conn.select_db('tingshuo');
		cur = conn.cursor();
		sqlstr = "select id,unix_timestamp(createtime) as time, likecnt, uid, msg from message where id=%s " % (msgid)
		print sqlstr
		result = cur.execute(sqlstr);
		for id, time, likecnt, uid, msg in cur.fetchall():
			one = {};
			one["id"]	= id;
			one["msg"]	= msg;
			one["t"]	= time;
			one["uid"]	= uid;
			one["like"]	= likecnt;
			jsonstr = json.dumps(one);
			msgs.append(jsonstr);
		print msgs;
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_user_info(acc):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "select id, nickname, avatar, gold, totallike from member where account=\"" + acc + "\"";
		print sql, acc;
		print "\n";
		result = cur.execute(sql);

		nik = "";
		avt = "";
		gld = 0;
		lik = 0;
		uid = 0;
		for id, nickname , avatar, gold , totallike in cur.fetchall():
			print id, nickname, avatar, gold, totallike;
			uid = id;
			nik = nickname;
			avt = avatar;
			gld = gold;
			lik = totallike;
		conn.commit();
		cur.close();
		conn.close();
	
		info = {};
		info["uid"] = uid;
		info["acc"] = acc;
		info["nik"] = nik;
		info["avt"] = avt;
		info["gold"] = gld;
		info["lik"] = lik;
		all = {};
		all["info"] = info;
		return json.dumps(all);
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";

def get_user_avatar(uin):
	try:
		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
		cur = conn.cursor()
		sql = "select avatar from member where userid=\"" + uin + "\"";
		print sql;
		print "\n";
		result = cur.execute(sql);
		avt = "";
		for  avatar in cur.fetchall():
			avt = avatar;
		conn.commit();
		cur.close();
		conn.close();
		return avt;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return "";
	

def valid_user(acc, passwd):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sql = "select account from member where account=\'"+acc+"\' and password=\'"+passwd+"\'";
		print sql; print '\n';
		result = cur.execute(sql);
		conn.commit();
		cur.close();
		conn.close();
		if result == 1:
			print "--valid user ", acc;
			return 1;
		else:
			print "--invalid user ", acc;
			return 0;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def getmd5(str):
	return hashlib.md5(src).hexdigest().upper();

def procLogon(acc, passwd):
	print acc, "is logon...";
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sql = "select * from member where account=\'"+acc+"\' and password=\'"+passwd+"\'";
		print sql; print '\n';
		result = cur.execute(sql);
		conn.commit();
		cur.close();
		conn.close();
		if result == 1:
			return 1;
		else:
			return 0;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
	
		
def procRegist(acc, passwd):
        print acc, "is regist...";
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
        	value = [acc, passwd]
		print value,'\n';
		result = cur.execute('insert into member(account, password) values(%s,%s)',value)
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def procModify(acc, passwd, item, value):
	print acc, "is modify ",item , "to ", value; 
	if 0 == valid_user(acc, passwd):
		return 0;
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		field = "nickname"
		if item=="psw":
			field = "password"
		elif item=="nk":
			field = "nickname"
		elif item=="g":
			field = "gender"
			if value!="m" and value!="f":
				return 0;
		elif item=="avt":
			field = "avatar"
		else:
			print "unkown modify item name"
			return 0;
			
		#value = [field, value, acc, passwd]
		sql = "update member set " + field + "=\'" + value +  "\' " + "where account=\'" + acc + "\' and password=\'" + passwd + "\'";
		print sql;
		result = cur.execute(sql);
		#result = cur.execute("update member set %s = %s where account=%s and password=%s", value);
		print result;
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def save_msg(acc, msg):
	print "save user(", acc, ") msg :" , msg , '\n';
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		uid = get_user_id(acc);
        	value = [uid, msg]
		result = cur.execute('insert into message(uid, msg) values(%s,%s)', value)
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
	
def get_unread_msg(acc, msgs, curpage, pagesize):
	try:
		#print "cur %s pagesize %s" % (curpage, pagesize)
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		readmsgno = get_user_read_msg_id(acc);
		sqlstr = "select id,unix_timestamp(createtime) as time, likecnt, uid, msg from message where id>%s and createtime>DATE_SUB(now(), INTERVAL 1 DAY) order by id DESC limit %s,%s" % (readmsgno, curpage, pagesize)
		print sqlstr
		result = cur.execute(sqlstr);
		for id, time, likecnt, uid, msg in cur.fetchall():
			one = {};
			one["id"]	= id;
			one["msg"]	= msg;
			one["t"]	= time;
			one["uid"]	= uid;
			one["like"]	= likecnt;
			jsonstr = json.dumps(one);
			msgs.append(jsonstr);
		print msgs;
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
	
def get_my_msg(uid, msgs, curpages, pagesize):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select id,unix_timestamp(createtime) as time, likecnt, uid, msg from message where uid=%s order by id DESC limit %s,%s" % (uid, curpages, pagesize)
		print sqlstr
		result = cur.execute(sqlstr);
		for id, time, likecnt, uid, msg in cur.fetchall():
			one = {};
			one["id"]	= id;
			one["msg"]	= msg;
			one["t"]	= time;
			one["uid"]	= uid;
			one["like"]	= likecnt;
			jsonstr = json.dumps(one);
			msgs.append(jsonstr);
		print msgs;
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def dec_net_pkg(net, pkgtype):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "update netflowpkg set remainder=remainder-1 where net=%s and pkgtype=%s and remainder>0" % (net, pkgtype)
		print sqlstr
		cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_all_skill():
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select type,name,consume,effect from skill";
		print sqlstr
		result = cur.execute(sqlstr);
		list = [];
		for type, name, consume, effect in cur.fetchall():
			one = {};
			one["type"]		= type;
			one["name"]		= name;
			one["consume"]		= consume;
			one["effect"]		= effect;
			list.append(one);
		conn.commit();
		cur.close();
		conn.close();
		return json.dumps(list);

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_net_pkg_list():
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select net,pkgtype,remainder from netflowpkg";
		print sqlstr
		result = cur.execute(sqlstr);
		list = [];
		for net, pkgtype, remainder in cur.fetchall():
			one = {};
			one["net"]		= net;
			one["pkgtype"]		= pkgtype;
			one["remainder"]	= remainder;
			list.append(one);
		conn.commit();
		cur.close();
		conn.close();
		return json.dumps(list);
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;


def get_msg_skill_list(msgid):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select usetime,sender,skilltype from msgskilllist where msgid=%s order by usetime desc" % (msgid);
		print sqlstr
		result = cur.execute(sqlstr);
		list = [];
		for usetime,sender,skilltype in cur.fetchall():
			print usetime, sender, skilltype
			one = {};
			one["time"]	= str(usetime);
			one["sender"]	= str(sender);
			one["skilltype"]= str(skilltype);
			list.append(one);
		print list
		conn.commit();
		cur.close();
		conn.close();
		return json.dumps(list);

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def save_use_skill_history(msgid, u, skilltype):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "insert into msgskilllist(msgid,skilltype,sender) values(%s,%s,%s)" % (msgid, skilltype, u);
		print sqlstr
		result = cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
	
	
def check_use_skill_gold(uid, skilltype, msgid):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr1 = "select a.gold from member a, skill b where a.id=%s and b.type=%s and a.gold>b.consume" % (uid, skilltype);
		print sqlstr1;
		result = cur.execute(sqlstr1);
		conn.commit();
		cur.close();
		conn.close();
		return result; 
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def check_msg_exist(msgid):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select id from message where id=%s" % (msgid);
		print sqlstr;
		result = cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return result; 
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def use_skill_to_msg(uid, skilltype, msgid):
	print "222222222222222222222222222"
	print skilltype;
	sqlstr = "*****";
	#add like
	if skilltype=="0":
		sqlstr = "update message b,skill c set b.likecnt=b.likecnt+1 where b.id=%s and c.type=%s" % (msgid, skilltype);
	#add gold
	elif skilltype=="1":
		sqlstr = "update member a, message c set a.gold=a.gold+1 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="2":
		#not complete
		sqlstr = "select 1;"
	elif skilltype=="5":
		#momoda . add 20 gold
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="6":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="7":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="8":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="9":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="10":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="11":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="12":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="13":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	elif skilltype=="14":
		sqlstr = "update member a, message c set a.gold=a.gold+20 where a.id=c.uid and c.id=%s" % (msgid);
	else:
		#do nothing
		sqlstr = "select 1";
	try:
		print "333333333333333333333333333"
       		conn  = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		print sqlstr;
		result = cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return result;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def dec_skill_gold(uid,skilltype):
	try:
       		conn  = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "update member a, skill b set a.gold=a.gold-b.consume where a.id=%s and b.type=%s" % (uid, skilltype);
		print sqlstr;
		result = cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return result;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

	
def getDBConn(dbname):
	print "teste----------------"
	print  DB_HOST, DB_NAME, DB_USER, DB_PASSWD
	print "teste----------------"
        conn=MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWD, port=3306,charset="utf8")
        return conn

class MainHandler(tornado.web.RequestHandler):
        def get(self):
		#testjson();
                t = self.get_argument('type');
                if t=="reg":
                	print "start reg..."
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			r = procRegist(acc, pas);
			if r == 1:
                		self.write("regist ok.")
			elif r == 0:
                		self.write("regist failed. account is used.")
			else:
                		self.write("regist failed.")
                elif t=="logon":
                	print "start logon..."

                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
                        r = procLogon(acc, pas)
			if r == 1:
                		self.write("logon ok.")
			else:
                		self.write("logon failed.")
		elif t=="modify":
			print "start modify..."
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			item= self.get_argument('item')
			value=self.get_argument('value')
                        r = procModify(acc, pas, item, value)
			if r == 1:
                		self.write("modify ok.")
			else:
                		self.write("modify failed.")

		elif t=="getinfo":
			print "get user info..."
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			#get user info
			if 1 == valid_user(acc, pas):
				info = get_user_info(acc);
				self.write(info);
	
		elif t=="hb":
			print "hart beat..."
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			cup = self.get_argument('curpage')
			pgs = self.get_argument('pagesize')
			r = valid_user(acc, pas)
			if r == 1:
				msgs = [];
				get_unread_msg(acc, msgs, cup, pgs);
				for msg in msgs:
					#print msg;
					self.write(msg);
			else:
				self.write('hb err');
		elif t=="msg":
			print ""
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			r = valid_user(acc, pas)
			if r == 1:
				msg = self.get_argument('msg');
				sr = save_msg(acc, msg.encode('utf8'));
				if sr==1:
					self.write("pub msg ok");
				else:
					self.write("pub msg failed");
			else:
				self.write('recv msg err');
		elif t=="query_u_info":
			#acc = self.get_argument('acc');
                	#pas = self.get_argument('psw')
			uid = self.get_argument('uid');
			#r = valid_user(acc, pas)
			r = 1
			if r == 1:
				acc = get_user_acc(uid);
				info = get_user_info(acc);
				#print jsonstr;
				self.write(info);
			else:
				self.write('invalid user');
		elif t=="like":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			msgid = self.get_argument('msgid');
			r = valid_user(acc, pas)
			if r == 1:
				sr = add_like(msgid);
				if sr==1:
					self.write("add like ok");
					uid = get_user_id(acc)
					save_use_skill_history(msgid, uid, SKILLTYPE['addlikenormal']);
				else:
					self.write("add like failed");
			else:
				self.write('recv msg err');
		elif t=="addgold":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			num = self.get_argument('num');
			r = valid_user(acc, pas)
			if r == 1:
				uid = get_user_id(acc)
				sr = add_gold(uid, num);
				if sr==1:
					self.write("add gold ok");
				else:
					self.write("add gold failed");
			else:
				self.write('recv msg err');
		elif t=="delgold":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			num = self.get_argument('num');
			r = valid_user(acc, pas)
			if r == 1:
				uid = get_user_id(acc);
				sr = del_gold(uid, num);
				if sr==1:
					self.write("del gold ok");
				else:
					self.write("del gold failed");
			else:
				self.write('recv msg err');

		elif t=="delmsg":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			msgid = self.get_argument('msg');
			r = valid_user(acc, pas)
			if r == 1:
				uid = get_user_id(acc);
				ret = del_msg(uid, msgid);
				if ret == 1:
					self.write("del msg ok");
				else:
					self.write("del msg failed");

			else:
				self.write('invalid acc');

		elif t=="getmsg":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			msgid = self.get_argument('msgid');
			r = valid_user(acc, pas)
			if r == 1:
				uid = get_user_id(acc);
				msgs = [];
				ret = get_msg(msgid, msgs);
				for msg in msgs:
					#print msg;
					self.write(msg);
			else:
				self.write('invalid acc');

		elif t=="daylike":
			acc = self.get_argument('acc');
                	pas = self.get_argument('psw')
			r = valid_user(acc, pas)
			if r == 1:
				u = get_user_id(acc);
				if u != 0:
					tlike = 0;
					ylike = 0;
					tlike, ylike = get_day_like(u);

					likes = {};
					likes["todaylike"] = tlike;
					likes["yesterdaylike"] = ylike;
					self.write(json.dumps(likes));
					
				else:
					self.write('invalid user. can not request this info');
			

			else:
				self.write('recv msg err');
		elif t=="postlist":
			print "get post list..."
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			cup = self.get_argument('curpage')
			pgs = self.get_argument('pagesize')
			r = valid_user(acc, pas)
			if r == 1:
				u = get_user_id(acc);
				if u != 0:
					msgs = [];
					get_my_msg(u, msgs, cup, pgs);
					for msg in msgs:
						self.write(msg);
			else:
				self.write('get post list err');

		elif t=="netpkg":
			print "get netpkg"
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			sub = self.get_argument('subt');
			if sub == "get":
				list = get_net_pkg_list();
				self.write(list);
			
			elif sub == "dec":
				r = valid_user(acc, pas)
				if r == 1:
					u = get_user_id(acc);
					if u != 0:
						net = self.get_argument('net');
						pkgtype = self.get_argument('pkgtype');
						dec_net_pkg(net, pkgtype);
						self.write('dec pkg ok');
					else:
						self.write('dec pkg  err');
				else:
					self.write('dec pkg  err');
			else:
				self.write("op error");
		
		elif t=="getallskill":
			skilllist = get_all_skill();
			self.write(skilllist);

		elif t=="useskill":
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			r = valid_user(acc, pas) 
			if r != 1:
				self.write("invalid user");
			else:
				u = get_user_id(acc);
				if u == 0:
					self.write("invalid user");
				msgid= self.get_argument('msgid');
				skilltype = self.get_argument('skilltype');
				check = check_use_skill_gold(u, skilltype, msgid);
				# 0 is success
				if check == 0:
					self.write("gold not enough");

				check = check_msg_exist(msgid);	
				if check == 0:
					self.write("msg not exist");

				result = use_skill_to_msg(u,skilltype, msgid);
				print result
				if result == 1:
					#decrease gold
					dec_skill_gold(u, skilltype);
					self.write("ok");

					#save history record
					save_use_skill_history(msgid, u, skilltype);
				else:
					self.write("unkown error");

		elif t=="getmsgskill":
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			r = valid_user(acc, pas) 
			if r != 1:
				self.write("invalid user");
			else:
				u = get_user_id(acc);
				if u == 0:
					self.write("invalid user");
				else:
					msgid = self.get_argument('msgid');
					msgskilllist = get_msg_skill_list(msgid);
					print msgskilllist;
					self.write(msgskilllist); 

		elif t=="getuseravatar":
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			r = valid_user(acc, pas) 
			if r != 1:
				self.write("invalid user");
			else:
				uin = self.get_argument('uin');
				avatar = get_user_avatar(uin);
				self.write(avatar);

		elif t=="comment":
                	acc = self.get_argument('acc')
                	pas = self.get_argument('psw')
			sub = self.get_argument('sub');
			r = valid_user(acc, pas) 
			if r == 1:
				#check msg valid
				#validmsg = check_msg(msgid)
				validmsg = 1
				if validmsg == 1:
					if sub == "get":
						msgid = self.get_argument('msg');
						cmts = [];
						get_all_comment(msgid, cmts);
						for cmt in cmts:
							self.write(cmt);
					elif sub == "post":
						msgid = self.get_argument('msg');
						cmt = self.get_argument('contents');
						receiver = self.get_argument('sendto', None);
						if receiver:
							sendtoid = get_user_id(receiver);
						else:
							sendtoid = 0;
						uid = get_user_id(acc);
						res = save_msg_comment(msgid, uid, sendtoid, cmt.encode('utf8'))
						if res == 1:
							self.write("post comment ok");
						else:
							self.write("post comment failed");
					elif sub == "cmtnum":
						msgid = self.get_argument('msg');
						num = get_comment_num(msgid)
						self.write(str(num));
					elif sub == "getnew":
						uid = get_user_id(acc);
						timepoint = self.get_argument('lasttime');
						cmts = [];
						get_my_new_comment(uid, timepoint, cmts);
						for cmt in cmts:
							self.write(cmt);
					elif sub == "getall":
						uid = get_user_id(acc);
						cup = self.get_argument('curpage', None)
						pgs = self.get_argument('pagesize', None)
						cmts = [];

						if cup and pgs:
							get_my_all_comment(uid, cup, pgs, cmts);
						else:
							get_my_all_comment(uid, 0, 1000, cmts);

						for cmt in cmts:
							self.write(cmt);
					elif sub == "getall2":
						uid = get_user_id(acc);
						cup = self.get_argument('curpage', None)
						pgs = self.get_argument('pagesize', None)
						cmts = [];
						get_my_all_comment_2(uid, cup, pgs, cmts);
						for cmt in cmts:
							self.write(cmt);
					elif sub == "getallsent":
						uid = get_user_id(acc);
						cup = self.get_argument('curpage', None)
						pgs = self.get_argument('pagesize', None)
						cmts = [];

						if cup and pgs:
							get_my_all_sent_comment(uid, cup, pgs, cmts);
						else:
							get_my_all_sent_comment(uid, 0, 1000, cmts);

						for cmt in cmts:
							self.write(cmt);
					elif sub == "getallsent2":
						uid = get_user_id(acc);
						cup = self.get_argument('curpage', None)
						pgs = self.get_argument('pagesize', None)
						cmts = [];
						get_my_all_sent_comment_2(uid, cup, pgs, cmts);
						for cmt in cmts:
							self.write(cmt);
					else:
						self.write("invalid sub operation");
				else:
					self.write("invalid msg id");
			else:
				self.write("invalid user");
			


                else:
                	self.write("invalid op type")

def get_my_all_sent_comment(uid, currentpage, pagesize, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select msgid, sender, cmt from msgcomment where sender=%u order by time desc limit %s, %s" % (uid, currentpage, pagesize)
		print sqlstr

		result = cur.execute(sqlstr);
		for msgid, sender, cmt in cur.fetchall():
			comments.append(cmt);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_my_all_sent_comment_2(uid, currentpage, pagesize, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select msgid, sender, cmt from msgcomment where sender=%u order by time desc limit %s, %s" % (uid, currentpage, pagesize)
		print sqlstr

		result = cur.execute(sqlstr);
		for msgid, sender, cmt in cur.fetchall():
			one = {};
			one["msgid"] = msgid;
			one["cmt"]   = cmt;
			jsonstr = json.dumps(one);
			comments.append(one);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_my_all_comment(uid, currentpage, pagesize, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select a.msgid as msgid, a.sender as sender, a.cmt as cmt from msgcomment a, message b where (b.uid=%u and a.msgid=b.id) or (b.uid!=%u and a.msgid=b.id and a.receiver=%u) order by a.time desc limit %s, %s" % (uid, uid, uid, currentpage, pagesize)
		print sqlstr

		result = cur.execute(sqlstr);
		for msgid, sender, cmt in cur.fetchall():
			comments.append(cmt);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
def get_my_all_comment_2(uid, currentpage, pagesize, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select a.msgid as msgid, a.sender as sender, a.cmt as cmt from msgcomment a, message b where (b.uid=%u and a.msgid=b.id and a.sender!=%u) or (b.uid!=%u and a.msgid=b.id and a.receiver=%u and a.sender!=%u) order by a.time desc limit %s, %s" % (uid, uid, uid, uid, uid,currentpage, pagesize)
		print sqlstr
		result = cur.execute(sqlstr);
		for msgid, sender, cmt in cur.fetchall():
			one = {};
			one["msgid"] = msgid;
			one["cmt"]   = cmt;
			jsonstr = json.dumps(one);
			comments.append(jsonstr);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_my_new_comment(uid, timepoint, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select a.msgid as msgid, a.sender as sender, a.cmt as cmt from msgcomment a, message b where (b.uid=%u or a.receiver=%u) and a.sender !=%u and a.msgid=b.id and a.time>from_unixtime(%s) order by a.time desc" % (uid, uid, uid, timepoint)
		print sqlstr

		result = cur.execute(sqlstr);
		for msgid, sender, cmt in cur.fetchall():
			comments.append(cmt);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;


def get_all_comment(msgid, comments):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select msgid, sender, unix_timestamp(time) as tm, cmt from msgcomment where msgid=%s order by time desc " % (msgid)
		print sqlstr

		result = cur.execute(sqlstr);
		for msgid, sender, tm, cmt in cur.fetchall():
			comments.append(cmt);
		print comments;
		conn.commit();
		cur.close();
		conn.close();
		return 1;

	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def save_msg_comment(msgid, senderid, receiverid, cmt):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
        	value = [msgid, senderid,receiverid, cmt]
		result = cur.execute('insert into msgcomment(msgid, sender, receiver,cmt) values(%s,%s,%s,%s)', value)
		conn.commit();
		cur.close();
		conn.close();
		return 1;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_comment_num(msgid):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select count(1) as num from msgcomment where msgid=%s" % (msgid)
		number = 0;
		result = cur.execute(sqlstr);
		for num in cur.fetchall():
			number = num
		conn.commit();
		cur.close();
		conn.close();
		return number;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;

def get_day_like(uid):
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "select todaylike, yesterdaylike from member where id=%u" % (uid)
		print sqlstr
		result = cur.execute(sqlstr);
		tl = 0;
		yl = 0;
		for todaylike, yesterdaylike in cur.fetchall():
			tl = todaylike;
			yl = yesterdaylike;
		conn.commit();
		cur.close();
		conn.close();
		return (tl, yl);
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0, 0;


def now():
	return str( time.strftime( '%Y-%m-%d %H:%M:%S' , time.localtime() ) )

def exchange_like_num():
	print "exchange today like num"
	try:
       		conn = getDBConn('''tingshuo''')
		conn.select_db('tingshuo')
        	cur=conn.cursor()
		sqlstr = "update member set yesterdaylike=todaylike, todaylike=0"
		print sqlstr
		cur.execute(sqlstr);
		conn.commit();
		cur.close();
		conn.close();
		return ;
	except MySQLdb.Error, e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])
		return 0;
	


application = tornado.web.Application([ 
    (r"/", MainHandler),
])  

def mainprocess():
	print "thread mainprocess start..."
	application.listen(80)
	db_init();
	tornado.ioloop.IOLoop.instance().start();

def timetick():
	print "thread timetick start..."
	db_init();
	sleep(5);
	while (1) :
		sleep(2);
		if time.localtime().tm_hour == 22 and time.localtime().tm_min == 59 :
			print time.ctime();
			exchange_like_num();
			sleep(60);

def main():
	print 'tingshuo server starting at:', now();
	db_init();
	threadpool = []
	t1 = threading.Thread(target=mainprocess);
	threadpool.append(t1);
	t2 = threading.Thread(target=timetick);
	threadpool.append(t2);

	t1.start();
	t2.start();

	threading.Thread.join(t1);
	threading.Thread.join(t2);
	print 'tingshuo server shutdown at:', now();

def handler(signum, frame):
	global is_exit
     	is_exit = True
     	print "receive a signal %d, is_exit = %d"%(signum, is_exit)

if __name__ == "__main__":
	signal.signal(signal.SIGINT, handler);
	signal.signal(signal.SIGTERM, handler);
	main();

