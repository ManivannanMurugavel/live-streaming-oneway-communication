import uuid
import redis
import time
import json
from flask_cors import CORS
from flask import Flask, request, render_template, Response

app = Flask(__name__)
CORS(app)
senderUsersLists = {}
receiverUserLists = {}
# r = redis.Redis(host='localhost', port=6379, db=0)
# p = r.pubsub()

@app.route('/')
def index():
    return render_template('Live Stream Example')

@app.route('/saveuser')
def saveuser():
	try:
		r = redis.Redis(host='localhost', port=6379, db=0)
		p = r.pubsub()
		name = request.args.get('name')
		usertype = request.args.get('type')
		uniqueid = uuid.uuid4().hex
		if(usertype == "sender"):
			senderUsersLists[uniqueid] = name
		elif(usertype == "receiver"):
			receiverUserLists[uniqueid] = name
			r.publish('receiver', json.dumps({uniqueid:name}))
		else:
			return "else error"
		# print(request.args.get('name'))
		return uniqueid
	except Exception as ex:
		# print(str(ex))
		return "exception error"

@app.route("/getusername")
def getusername():
	try:
		name = request.args.get('token')
		usertype = request.args.get('type')
		if(usertype == "sender" and name in senderUsersLists):
			return senderUsersLists[name]
		elif(usertype == "receiver" and name in receiverUserLists):
			return receiverUserLists[name]
		else:
			return "error"
	except:
		return "error"

@app.route("/getallreceiver")
def getallreceiver():
	try:
		userid = request.args.get('token')
		if(userid in senderUsersLists):
			return receiverUserLists
		else:
			return "error"
	except:
		return "error"

@app.route("/sendmessage",methods=["POST"])
def sendmessage():
	try:
		if(request.method == "POST"):
			# print(request.form)
			sendertoken = request.form["senderToken"]
			receivertoken = request.form["receiverToken"]
			message = request.form["message"]
			if(sendertoken not in senderUsersLists):
				return "error"
			sendername = senderUsersLists[sendertoken]
			r = redis.Redis(host='localhost', port=6379, db=0)
			r.publish(receivertoken, json.dumps({"name":sendername,"message":message}))
			return "success"
		else:
			return "error"
	except:
		return "error"

@app.route("/getlivereceiver")
def getlivereceiver():
	def streamuser():
		try:
			r = redis.Redis(host='localhost', port=6379, db=0)
			p = r.pubsub()
			p.subscribe('receiver')
			while True:
				message = p.get_message()
				if message and message['data'] != 1:
					print(message['data'].decode('utf-8'))
					yield 'data:' + message['data'].decode('utf-8') + '\n\n'
				time.sleep(1)
		except Exception as ex:
			print(str(ex))
			pass
	return Response(response = streamuser(),status=200, mimetype= 'text/event-stream')

@app.route("/receivemessage/<token>")
def receivemessage(token):
	def livemessage(token):
		try:
			r = redis.Redis(host='localhost', port=6379, db=0)
			p = r.pubsub()
			p.subscribe(token)
			while True:
				message = p.get_message()
				if message and message['data'] != 1:
					# print("messgae")
					# print(message['data'].decode('utf-8'))
					yield 'data:' + message['data'].decode('utf-8') + '\n\n'
				time.sleep(1)
		except Exception as ex:
			print(str(ex))
			pass
	return Response(response = livemessage(token),status=200, mimetype= 'text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)