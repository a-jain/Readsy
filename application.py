from flask import Flask, render_template, flash, url_for, request, redirect, abort
from flask import send_from_directory, safe_join
from werkzeug.utils import secure_filename
from hashlib import sha1
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
# from boto.s3.connection import S3Connection
# from boto.s3.key import Key

# conn = S3Connection('____________________', '________________________________________')
# bucket = conn.get_bucket('bucketname')
# key = bucket.get_key("picture.jpg")
# fp = open ("picture.jpg", "w")
# key.get_file (fp)
import re, sys, json, os, base64, hmac, urllib, time
import HTMLParser
reload(sys)
sys.setdefaultencoding("utf-8")

application = Flask(__name__)
application.debug = True
application.secret_key = '\x99\x02~p\x90\xa3\xce~\xe0\xe6Q\xe3\x8c\xac\xe9\x94\x84B\xe7\x9d=\xdf\xbb&'

# conn = S3Connection()

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

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
	maxpages = 0
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
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#######################################################

@application.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

@application.errorhandler(500)
def special_exception_handler(error):
    return 'File doesn\'t exist', 500


#######################################################

@application.route('/')
@application.route('/spritzy/<filename>')
def spritz(filename=None):
	if not filename:
		return render_template('spritz.html', text="")

	# flask.safe_join(directory, filename)
	url = "http://spritzy.s3-website-us-east-1.amazonaws.com/" + filename
	url = UPLOAD_FOLDER + filename
	url = safe_join(application.config['UPLOAD_FOLDER'], filename)
	print url
	s = convert_pdf_to_txt(url)
	s = re.sub(r'\s+', ' ', s)
	s = s.replace('!', '')
	s = HTMLParser.HTMLParser().unescape(s)
	# print s
	
	return render_template('spritz.html', text=s) 


@application.route('/spritz/login_success')
def spritz_login():
	return render_template('login_success.html')


@application.route('/upload')
@application.route('/upload', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
			return redirect(url_for('spritz', filename=filename))
			# return redirect(url_for('uploaded_file', filename=filename))
	return render_template('upload_form.html')


@application.route('/uploads/<filename>')
def uploaded_file(filename):
	if not filename:
		return redirect(url_for('uploaded_file', filename=filename))

	return send_from_directory(application.config['UPLOAD_FOLDER'], filename)

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


if __name__ == '__main__':
	application.run(debug=True)