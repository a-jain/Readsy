# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, url_for, after_this_request, request, redirect, abort
from flask import send_from_directory, safe_join, json
from werkzeug.utils import secure_filename
from hashlib import sha1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError
from cStringIO import StringIO
from urlparse import urlparse
from flask.ext.sqlalchemy import SQLAlchemy
from flask_s3 import FlaskS3
from flask.ext.assets import Environment, Bundle
from flask_wtf import Form
from wtforms import TextField, widgets, RadioField, validators
from wtforms.fields import SelectMultipleField
from wtformsparsleyjs import StringField, SelectField
from sqlalchemy import create_engine, MetaData
from goose import Goose
from form import *

import MySQLdb
import re, regex, sys, os, base64, hmac, urllib, time, HTMLParser, requests, urllib2, gzip, functools, cssmin, stripe

reload(sys)
sys.setdefaultencoding("utf-8")

def start_app():
	app = Flask(__name__)
	app.config['S3_BUCKET_NAME'] = 'readsy'
	app.config['S3_CDN_DOMAIN'] = 'dwdhruapbuq08.cloudfront.net'
	app.config['S3_USE_HTTPS'] = False
	app.config['USE_S3_DEBUG'] = True # should be true
	app.config['AWS_ACCESS_KEY_ID'] = os.environ['AWS_ACCESS_KEY_ID']
	app.config['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_SECRET_ACCESS_KEY']
	
	s3 = FlaskS3()
	s3.init_app(app)

	assets = Environment()	
	# use closure_js once i have java 7
	js = Bundle('js/jquery.cookie.js', 'js/mousetrap.min.js', 'js/app.js', 'js/froala_editor.min.js', filters='rjsmin', output='gen/packed.js')
	css = Bundle('css/bootstrap.min.css', 'css/froala_editor.min.css', 'css/bootstrapcustom.css', filters='cssmin', output='gen/packed.css')
	assets.register('js_all', js)
	assets.register('css_all', css)
	app.config['ASSETS_DEBUG'] = False
	assets.init_app(app)
	app.config['FLASK_ASSETS_USE_S3'] = True #should be true

	return app

application = start_app()

# try:
	# db = MySQLdb.connect(host="akashjain.c5vtmzrmhbcb.us-east-1.rds.amazonaws.com", user="akashjain", passwd="akashjain", db="usertable")
	# db.autocommit(True)
# except:
# 	pass

application.config['COMPRESS_DEBUG'] = True

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
READABILITY_TOKEN = 'd58d28ee3b6259ece0a6f7b3ad985aa171fe8ac5'

ERROR_400 = 'Invalid file/URL for parsing. If you needed to log in to access the file, then download the file and upload it directly'
ERROR_401 = 'Ready\'s servers aren\'t authorised to access this file. Please upload it directly to us (or use Dropbox)'
ERROR_404 = 'This page does not exist'
ERROR_500 = 'File doesn\'t exist any more. If you just uploaded it, please try again'

####################################################### 

def gzipped(f):
	@functools.wraps(f)
	def view_func(*args, **kwargs):
		@after_this_request
		def zipper(response):
			accept_encoding = request.headers.get('Accept-Encoding', '')

			if 'gzip' not in accept_encoding.lower():
				return response

			response.direct_passthrough = False

			if (response.status_code < 200 or
				response.status_code >= 300 or
				'Content-Encoding' in response.headers):
				return response
			gzip_buffer = StringIO()
			gzip_file = gzip.GzipFile(mode='wb', 
									  fileobj=gzip_buffer)
			gzip_file.write(response.data)
			gzip_file.close()

			response.data = gzip_buffer.getvalue()
			response.headers['Content-Encoding'] = 'gzip'
			response.headers['Vary'] = 'Accept-Encoding'
			response.headers['Content-Length'] = len(response.data)

			return response

		return f(*args, **kwargs)

	return view_func

####################################################### 	

def convert_pdf_to_txt(path):
	rsrcmgr = PDFResourceManager()
	retstr = StringIO()
	codec = 'utf-8'
	laparams = LAParams()

	device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
	fp = file(path, 'rb')
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	password = ""
	maxpages = 120
	caching = True
	pagenos=set()
	# print "two"

	for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
		interpreter.process_page(page)
	# print "one"

	try:
		fp.close()
		device.close()
		str = retstr.getvalue()
		retstr.close()
	except:
		str = retstr.getvalue()

	return str

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#######################################################

@application.errorhandler(400)
def PDF_not_found(error):
	return render_template('spritz.html', text=ERROR_400, error=400)

@application.errorhandler(401)
def needAuth(error):
	return render_template('spritz.html', text=ERROR_401, error=401)

@application.errorhandler(404)
def page_not_found(error):
	return render_template('spritz.html', text=ERROR_404, error=404)

@application.errorhandler(500)
def special_exception_handler(error):
	return render_template('spritz.html', text=ERROR_500, error=500)
	
@application.route('/spritz/login_success')
def spritz_login():
	return render_template('login_success.html')

@application.route('/sign_s3/')
def sign_s3():
	AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
	AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
	S3_BUCKET = os.environ.get('S3_BUCKET')

	object_name = request.args.get('s3_object_name')
	mime_type = request.args.get('s3_object_type')

	expires = int(time.time()+10)
	amz_headers = "x-amz-acl:public-read"

	put_request = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, S3_BUCKET, object_name)

	signature = base64.encodestring(hmac.new(AWS_SECRET_KEY, put_request, sha1).digest())
	signature = urllib.quote_plus(signature.strip())

	url = 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, object_name)

	return json.dumps({
		'signed_request': '%s?AWSAccessKeyId=%s&Expires=%d&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature),
		 'url': url
	  })

#######################################################

def PDFhelper(url):
	try:
		s = convert_pdf_to_txt(url)
		print s
		s = HTMLParser.HTMLParser().unescape(s)
		s = re.sub(r'(?<=[a-z]\.)\n+', r'\\n\\n', s)
		# s = re.sub(r'  +', r' ', s)
		
		s = re.sub(r'\s+', ' ', s)
		s = clean(s)
		# print s
		return s

	except:
		abort(400)

def TXThelper(url):
	try:
		fp = open(url, 'r')
		s = fp.read(application.config['MAX_CONTENT_LENGTH'])
		s = s.encode('unicode-escape').decode()
		s = re.sub(r'\s+', ' ', s)
		return s

	except:
		abort(400)

def clean(s):
	PAT_INLINEFOOTNOTE = r'[\(\[\.,]\d{1,3}(?:[,–]\d{1,3}){0,2}[\)\]]?'
	PAT_MOREFOOTNOTES = r'(?<!\d)[0-9]{1,3}(?:[,\- \–][0-9]{1,3}){1,3}(?=[\.,])'
	PAT_FIGURE = r'\s?[\(\[]?[fF]ig\.? \d{1,3}[\)\]]?'
	PAT_FIGURES = r'\(cid:\d\d?\d?\) ?'
	PAT_RANDOMHYPHEN = r'(?<=[a-z])-\s(?=[a-z])'
	PAT_REFERENCES = r'REFERENCES\s.*'
	PAT_EXTRASPACE = r'  +'
	PAT_WEIRDFI = r'ﬁ ?'
	PAT_WEIRDFL = r'ﬂ ?'
	PAT_WEIRDNINO = r' ?˜n'
	PAT_FOOTNOTECONS = r'\d\d?.\d\d?.\d\d?.\d\d?'
	PAT_WEIRDPUNC = r' [.,\/:;)]'
	PAT_WEIRDPUNC2 = r'[(] '
	PAT_RANDOMDOT = r'[a-v]\.[a-z]'
	PAT_TABLE = r'(?<!\w)\w\w? \w\w? [\w:]\w?\.? \w[\w.]? '
	PAT_URL = r'(((ht|f)tps?\:\/\/)|~/|/)?([a-zA-Z]([\w\-]+\.)+([\w]{2,5})(:[\d]{1,5})?)/?(\w+\.[\w]{3,4})?((\?\w+=\w+)?(&\w+=\w+)*)'
	PAT_SINGLELETTERS = r' . . . '
	PAT_COPYRIGHT = r'(([cC]opyright)|©).*?[aA]ll rights reserved\.?'
	PAT_RANDONUM = r'(?<=[a-z]{3})\d{1,3}(?: [0-9]{1,3})?(?=[\. ,])'
	PAT_PAGEREF = r'\d\d? of \d\d? '
	PAT_MLA = r' \([12]\d\d\d\)'

	s = re.sub(PAT_REFERENCES, '', s)
	s = re.sub(PAT_COPYRIGHT, '', s, flags=re.I)
	s = re.sub(PAT_WEIRDFI, 'fi', s)
	s = re.sub(PAT_WEIRDFL, 'fl', s)
	s = re.sub(PAT_WEIRDNINO, 'ñ', s)
	s = re.sub(PAT_RANDOMHYPHEN, '', s)
	s = re.sub(PAT_INLINEFOOTNOTE, '', s)
	s = re.sub(PAT_MOREFOOTNOTES, '', s)
	s = re.sub(PAT_FIGURE, '', s)
	s = re.sub(PAT_FIGURES, '', s)
	s = re.sub(PAT_PAGEREF, '', s)
	s = re.sub(PAT_RANDOMDOT, '', s)
	s = re.sub(PAT_FOOTNOTECONS, '', s)
	s = re.sub(PAT_TABLE, '', s)
	s = re.sub(PAT_URL, '', s)
	s = re.sub(PAT_RANDONUM, '', s)
	s = re.sub(PAT_WEIRDPUNC2, '', s)
	s = re.sub(PAT_WEIRDPUNC, '', s)
	s = re.sub(PAT_EXTRASPACE, ' ', s)
	s = re.sub(PAT_SINGLELETTERS, '', s)
	s = re.sub(PAT_MLA, '', s)

	return s

def cleantext(s):
	PAT_PHOTOGRAPHER = r'Photographer:.*?\n'
	PAT_CLOSE = r'\n.*?Close\n'
	PAT_OPEN = r'\n.*?Open\n'
	PAT_COPYRIGHT = r'(([cC]opyright)|©).*?[aA]ll rights reserved\.?'
	PAT_PERIOD = r'(?<=[a-z])\.(?=[A-Z])'

	s = re.sub(PAT_COPYRIGHT, '', s, flags=re.I)
	s = re.sub(PAT_PHOTOGRAPHER, '', s)
	s = re.sub(PAT_CLOSE, '', s)
	s = re.sub(PAT_OPEN, '', s)
	s = re.sub(PAT_PERIOD, r'. ', s)

	s = re.sub(r'(?<=[.!?"”])\n+', r' \\n\\n', s)
	s = re.sub(r'\n+', r' ', s)

	return s

#######################################################

@application.route('/contact')
@application.route('/about')
@application.route('/home')
@application.route('/text')
@application.route('/')
@gzipped
def index():
	return render_template('spritz.html')

@application.route('/spritzy')
@application.route('/spritzy/<filename>')
@gzipped
def spritz(filename=None):
	if not filename:
		return redirect(url_for('index'))

	# url = "http://spritzy.s3-website-us-east-1.amazonaws.com/" + filename
	url = safe_join(application.config['UPLOAD_FOLDER'], filename)
	# print url
	if not os.path.isfile(url):
		abort(500)

	if filename.split('.')[-1].lower() == "txt":
		s = TXThelper(url)
		return render_template('spritz.html', text=s, filename=filename, titleText=filename) 

	elif filename.split('.')[-1].lower() == "pdf":
		s = PDFhelper(url)
		return render_template('spritz.html', text=s, filename=filename, titleText=filename) 

	return redirect(url_for('index'))

# @application.route('/upload')
@application.route('/upload', methods=['GET', 'POST'])
@gzipped
def upload_file():
	if request.method == 'POST':
		try:
			file = request.files['file']
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
				return redirect(url_for('spritz', filename=filename))
		except:
			abort(400)
	
	return redirect(url_for('index'))

# text only
@application.route('/text', methods=['GET', 'POST'])
@gzipped
def POSTtexthandler():
	if request.method == 'POST':
		text = request.form['text']
		print text
		return render_template('spritz.html', text=text, filename="test1", titleText="test2") 

	return redirect(url_for('index'))

@application.route('/text/<parseString>')
@gzipped
def texthandler(parseString=None):
	# s = re.sub(r'%0A', r'\n', parseString)
	# s = re.sub(r'\n+', r'\\n\\n', parseString)
	s = urllib2.url2pathname(parseString)
	s = re.sub(r'\n+', r'\\n\\n', s)
	print s

	return render_template('spritz.html', text=s, filename="", titleText="Highlighted Text") 

@application.route('/web')
@gzipped
def url_handle():
	url = request.args.get('url', '')

	if not url or url == '':
		return redirect(url_for('index'))

	if "auth=1" in url.split("&"):
		abort(401)
	
	if '://' not in url:
		url = "http://" + url

	if "readsy.co" in url:
		return render_template('spritz.html', text="Try parsing a different website!")

	ext = url.split('.')[-1].lower()
	if ext in ALLOWED_EXTENSIONS:
		try:
			r = requests.get(url, stream=True)
		except:
			abort(400)

		if 'content-length' in r.headers:
			if int(r.headers['content-length']) > application.config['MAX_CONTENT_LENGTH']:
				abort(400)

		if r.status_code == 200:
			fullname = url.split('/')[-1]
			filename = fullname.split('.')[0]
			path = safe_join(application.config['UPLOAD_FOLDER'], fullname)
			with open(path, 'wb') as f:
				for chunk in r.iter_content():
					f.write(chunk)
			if ext == "pdf":
				s = PDFhelper(path)
				return render_template('spritz.html', text=s, filename=fullname, titleText=fullname) 

			elif ext == "txt":
				s = TXThelper(path)
				return render_template('spritz.html', text=s, filename=fullname, titleText=fullname)

		else:
			abort(400)
			return

	try:
		g = Goose()
		article = g.extract(url=url)
		s = cleantext(article.cleaned_text)
		# if article.top_image:
		# 	img = article.top_image
		return render_template('spritz.html', text=s, filename=url.split('//')[1], titleText=article.title)
	except:
		abort(400)

###################################################

@application.route('/test')
@application.route('/test', methods=('GET', 'POST'))
def test():
	textSelector = TextSelect(csrf_enabled=False)
	userSurvey1 = UserSurvey1(csrf_enabled=False)

	if userSurvey1.validate_on_submit():
		cursor = db.cursor()
		cursor.execute("SET net_write_timeout=3600")

		allDifficulties = ', '.join(userSurvey1.difficulties.data)

		# NB temporarily set learning difficulties to just take first selected
		sql = "INSERT INTO usertable.userids (country, ageRange, readingIssue, nativeLang, device) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (userSurvey1.country.data, userSurvey1.agerange.data, allDifficulties, userSurvey1.nativelang.data, userSurvey1.deviceused.data)
		print sql
		try:
			cursor.execute(sql)
		except:
			abort(404)
		userId = int(cursor.lastrowid)

		try:
			cursor.execute("INSERT INTO usertable.questionnaire1 (userId, q1, q2, q3, q4, q5) VALUES (%d, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (userId, userSurvey1.aq1.data, userSurvey1.aq2.data, userSurvey1.aq3.data, userSurvey1.aq4.data, userSurvey1.aq5.data))
			cursor.execute("INSERT INTO usertable.questionnaire2 (userId, q1, q2, q3, q4, q5) VALUES (%d, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (userId, userSurvey1.bq1.data, userSurvey1.bq2.data, userSurvey1.bq3.data, userSurvey1.bq4.data, userSurvey1.bq5.data))
		except:
			abort(400)

		cursor.close()
		
		return render_template('success.html')
	return render_template('testsite.html', textSelector=textSelector, userSurvey1=userSurvey1)

@application.route('/results')
def results():
	allUsers = "SELECT * FROM usertable.userids;"
	allQ1 = "SELECT * FROM usertable.questionnaire1;"
	allQ2 = "SELECT * FROM usertable.questionnaire2;"

	cursor = db.cursor()

	cursor.execute(allUsers)
	allUsersResults = cursor.fetchall()
	# print allUsersResults

	cursor.execute(allQ1)
	allQ1Results = cursor.fetchall()
	# print allQ1Results

	cursor.execute(allQ2)
	allQ2Results = cursor.fetchall()
	# print allQ2Results

	cursor.close()

	return render_template('results.html', allUsersResults=json.dumps(allUsersResults), allQ1Results=json.dumps(allQ1Results), allQ2Results=json.dumps(allQ2Results))

###################################################

if __name__ == '__main__':
	application.run(debug=True, port=5000)
