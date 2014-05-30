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
# from readability import ParserClient
from urlparse import urlparse
# from bs4 import BeautifulSoup
from flask.ext.sqlalchemy import SQLAlchemy
from flask_s3 import FlaskS3
from flask.ext.assets import Environment, Bundle
from flask_wtf import Form
from wtforms import TextField, widgets, RadioField, validators
# from wtforms.validators import DataRequired
from wtforms.fields import SelectMultipleField
from wtformsparsleyjs import StringField, SelectField
from sqlalchemy import create_engine, MetaData
from goose import Goose

import MySQLdb
import re, regex, sys, os, base64, hmac, urllib, time, HTMLParser, requests, urllib2, gzip, functools, cssmin, pycountry, stripe

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
	js = Bundle('js/jquery.cookie.js', 'js/app.js', 'js/froala_editor.min.js', filters='rjsmin', output='gen/packed.js')
	css = Bundle('css/bootstrap.min.css', 'css/froala_editor.min.css', 'css/bootstrapcustom.css', filters='cssmin', output='gen/packed.css')
	assets.register('js_all', js)
	assets.register('css_all', css)
	app.config['ASSETS_DEBUG'] = False
	assets.init_app(app)
	app.config['FLASK_ASSETS_USE_S3'] = True #should be true

	return app

application = start_app()

db = MySQLdb.connect(host="akashjain.c5vtmzrmhbcb.us-east-1.rds.amazonaws.com", user="akashjain", passwd="akashjain", db="usertable")
db.autocommit(True)

application.config['COMPRESS_DEBUG'] = True

stripe_keys = {
    'secret_key':      os.environ['STRIPE_SECRET_KEY'],
    'publishable_key': os.environ['STRIPE_PUBLISHABLE_KEY'],
    'test_secret_key': os.environ['STRIPE_TEST_SECRET_KEY'],
    'test_publishable_key': os.environ['STRIPE_TEST_PUBLISHABLE_KEY']
}
stripe.api_key = stripe_keys['secret_key']
stripeKey = stripe_keys['publishable_key']
# print stripe.api_key

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
READABILITY_TOKEN = 'd58d28ee3b6259ece0a6f7b3ad985aa171fe8ac5'

ERROR_400 = 'Invalid file/URL for parsing'
ERROR_401 = 'Ready\'s servers aren\'t authorised to access this file. Please download and upload it directly to us (or use Dropbox)'
ERROR_404 = 'This page does not exist'
ERROR_500 = 'File doesn\'t exist any more'

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
	maxpages = 25
	caching = True
	pagenos=set()
	for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
		interpreter.process_page(page)
	fp.close()
	device.close()
	str = retstr.getvalue()
	retstr.close()
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
	PAT_FIGURES = r'\(cid:173\) ?'
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
	return render_template('spritz.html', key=stripeKey)

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
		return render_template('spritz.html', text=s, filename=filename, titleText=filename, key=stripeKey) 

	elif filename.split('.')[-1].lower() == "pdf":
		s = PDFhelper(url)
		return render_template('spritz.html', text=s, filename=filename, titleText=filename, key=stripeKey) 

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
		return render_template('spritz.html', text=text, filename="test1", titleText="test2", key=stripeKey) 

	return redirect(url_for('index'))

@application.route('/text/<parseString>')
@gzipped
def texthandler(parseString=None):
	# s = re.sub(r'%0A', r'\n', parseString)
	# s = re.sub(r'\n+', r'\\n\\n', parseString)
	s = urllib2.url2pathname(parseString)
	s = re.sub(r'\n+', r'\\n\\n', s)
	print s

	return render_template('spritz.html', text=s, filename="", titleText="Highlighted Text", key=stripeKey) 

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
		return render_template('spritz.html', text="Try parsing a different website!", key=stripeKey)

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
				return render_template('spritz.html', text=s, filename=fullname, titleText=fullname, key=stripeKey) 

			elif ext == "txt":
				s = TXThelper(path)
				return render_template('spritz.html', text=s, filename=fullname, titleText=fullname, key=stripeKey)

		else:
			abort(400)
			return

	try:
		g = Goose()
		article = g.extract(url=url)
		s = cleantext(article.cleaned_text)
		# if article.top_image:
		# 	img = article.top_image
		return render_template('spritz.html', text=s, filename=url.split('//')[1], titleText=article.title, key=stripeKey)
	except:
		abort(400)

@application.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = 300

    customer = stripe.Customer.create(
        email='customer@example.com',
        card=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Flask Charge'
    )

    return render_template('spritz.html', text="Thank you so much for donating! I really appreciate it.", filename="Thanks!", titleText="Thanks!", amount=amount)

###################################################

class TextSelect(Form):
	texts=[("http://readsy.co/static/txt/ironman.html", "Iron Man"), ("http://readsy.co/static/txt/gulls.html", "Gulls")]
	textChooser = SelectMultipleField('Text to be Spritzed', choices=texts)

class NewUser(Form):
	cc = {}
	t = list(pycountry.countries)
	for country in t:
		cc[country.alpha2]=country.name
	cc = [(v, k) for k, v in cc.iteritems()]
	cc.sort()
	cc = [(v, k) for k, v in cc]

	age = [("u10", "Under 10"), ("11-20", "11-20"), ("21-40", "21-40"), ("41-60", "41-60"), ("61-80", "61-80"), ("o81", "Over 81")]
	allDifficulties = [("AMD", "Age Related Macular Degeneration"), ("BI", "Brain Injury"), ("D", "Dyslexia"), ("VI", "Vision Issues"), ("O", "Other"), ("N", "None")]
	nativelang = [("yes", "Yes"), ("no", "No")]
	device = [("desktop", "Desktop"), ("laptop", "Laptop"), ("tablet", "Tablet"), ("mobile", "Smartphone")]

	cc.insert(0, (None, ""))
	age.insert(0, (None, ""))

	country = SelectField('Country', [validators.DataRequired(message='Sorry, this is a required field.')], choices=cc)
	agerange = SelectField('Age Range', [validators.DataRequired(message='Sorry, this is a required field.')], choices=age)
	difficulties = SelectMultipleField('Reading Difficulties (select all that apply)', [validators.DataRequired(message='Sorry, this is a required field.')], choices=allDifficulties, coerce=unicode, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
	nativelang = RadioField('Is English your native language?', [validators.DataRequired(message='Sorry, this is a required field.')], choices=nativelang)
	deviceused = RadioField('What device are you using?', [validators.DataRequired(message='Sorry, this is a required field.')], choices=device)

class UserSurvey1(Form):
	aq1_label = "How tall was the Iron Man?"
	aq2_label = "His eyes were like?"
	aq3_label = "What flew over and landed?"
	aq4_label = "What did they have on the cliff?"
	aq5_label = "What did the seagull pick up first?"

	aq1_answers = [("a", "very tall"), ("b", "short"), ("c", "taller than a house"), ("d", "taller than a boulder")]
	aq2_answers = [("a", "headlamps"), ("b", "rocks"), ("c", "cats"), ("d", "flames")]
	aq3_answers = [("a", "a hummingbird"), ("b", "a bat"), ("c", "two seagulls"), ("d", "a plane")]
	aq4_answers = [("a", "a houseboat"), ("b", "two chicks in a nest"), ("c", "a nest"), ("d", "a drum of oil")]
	aq5_answers = [("a", "nothing"), ("b", "a finger"), ("c", "a knife blade"), ("d", "one of the Iron Man's eyes")]

	aq1 = RadioField(aq1_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=aq1_answers)
	aq2 = RadioField(aq2_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=aq2_answers)
	aq3 = RadioField(aq3_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=aq3_answers)
	aq4 = RadioField(aq4_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=aq4_answers)
	aq5 = RadioField(aq5_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=aq5_answers)

	bq1_label = "What did the second seagull pickup?"
	bq2_label = "What color did the eye glow?"
	bq3_label = "What did the Iron Man try to pick up, stuck between the rocks?"
	bq4_label = "What was the eye doing when they found it?"
	bq5_label = "How did the legs move?"

	bq1_answers = [("a", "a clam"), ("b", "the right hand"), ("c", "a house"), ("d", "bridseed")]
	bq2_answers = [("a", "blue"), ("b", "purple"), ("c", "white"), ("d", "pink")]
	bq3_answers = [("a", "a hummingbird"), ("b", "the left arm"), ("c", "two seagulls"), ("d", "a plane")]
	bq4_answers = [("a", "waving"), ("b", "blinking at them"), ("c", "sleeping"), ("d", "nothing")]
	bq5_answers = [("a", "running"), ("b", "skip"), ("c", "with a limp"), ("d", "Hop, hop, hop, hop")]

	bq1 = RadioField(bq1_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=bq1_answers)
	bq2 = RadioField(bq2_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=bq2_answers)
	bq3 = RadioField(bq3_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=bq3_answers)
	bq4 = RadioField(bq4_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=bq4_answers)
	bq5 = RadioField(bq5_label, [validators.DataRequired(message='Sorry, this is a required field.')], choices=bq5_answers)

@application.route('/test')
@application.route('/test', methods=('GET', 'POST'))
def test():
	form = NewUser(csrf_enabled=False)
	textSelector = TextSelect(csrf_enabled=False)
	userSurvey1 = UserSurvey1(csrf_enabled=False)

	if form.validate_on_submit():
		cursor = db.cursor()

		sql = "INSERT INTO usertable.userids (country, ageRange, readingIssue, nativeLang, device) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (form.country.data, form.agerange.data, form.difficulties.data[0], form.nativelang.data, form.deviceused.data)
		print sql
		cursor.execute(sql)
		userId = int(cursor.lastrowid)

		cursor.execute("INSERT INTO usertable.questionnaire1 (userId, q1, q2, q3, q4, q5) VALUES (%d, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (userId, userSurvey1.q1.data, userSurvey1.q2.data, userSurvey1.q3.data, userSurvey1.q4.data, userSurvey1.q5.data))
		cursor.execute("INSERT INTO usertable.questionnaire2 (userId, q1, q2, q3, q4, q5) VALUES (%d, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');" % (userId, userSurvey2.q1.data, userSurvey2.q2.data, userSurvey2.q3.data, userSurvey2.q4.data, userSurvey2.q5.data))

		cursor.close()
		
		return render_template('success.html')
	return render_template('testsite.html', form=form, textSelector=textSelector, userSurvey1=userSurvey1)

###################################################

if __name__ == '__main__':
	application.run(debug=True, port=5000)
