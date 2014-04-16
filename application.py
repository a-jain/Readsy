import os.path
from flask import Flask, render_template, flash, url_for, request, redirect, abort
from flask import send_from_directory
from werkzeug.utils import secure_filename
import json
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
import re
import sys
import HTMLParser
reload(sys)
sys.setdefaultencoding("utf-8")

application = Flask(__name__)
application.debug = True
application.secret_key = '\x99\x02~p\x90\xa3\xce~\xe0\xe6Q\xe3\x8c\xac\xe9\x94\x84B\xe7\x9d=\xdf\xbb&'

UPLOAD_FOLDER = 'static/spritz/'
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

@application.route('/')
@application.route('/spritzy/<filename>')
def spritz(filename=None):
	if not filename:
		return render_template('spritz.html', text="")

	url = "static/spritz/" + filename
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
	

if __name__ == '__main__':
	application.run(debug=True)