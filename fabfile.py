from fabric.api import local

def run():
    local("python application.py")

def push(commitName="default"):
	local("git add -A")
	local("git commit -m %s" % commitName)
	local("git push")
	local("git push heroku master")

def s3():
	local("python s3upload.py")

def scale(num):
	local("heroku ps:scale web=%d" % int(num))

def newrelic():
	local("heroku addons:open newrelic")