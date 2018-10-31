# -*- coding: utf8 -*-

"""
Paquetes instalados con la opcion --user  :
python36 -m install PAQUETE --user
se instalan en el directorio : /home/joaquin/.local/lib/python3.6/site-packages
de forma que no necesitamos instalar con permiso de root, ver como se hace en hostinet
"""
import os, sys,  os.path
sys.path.insert(0, './Lib')

from flask import Flask, render_template, Markup, request, abort, redirect, url_for, session, escape, flash, g 
from flask import Blueprint
from flask.views import View
from flask_socketio import SocketIO
from werkzeug import secure_filename
import eventlet
import MyFuncPool18
import ChimoFunc18
import Myconfig
import asyncio
import time
import FuncFormMariaDb
import logging
import logging.handlers
import json
import queue
import threading

global numuser, DictConServer,  tab1,  logger

#-----------------------------------------------------------------------------------
class Thread(threading.Thread):
	def __init__(self, target, *args):
		threading.Thread.__init__(self, target=target, args=args)
		self.daemon=False
		self.start()
		self.nombre = ""
	def Nombre(self, nombre):
		self.nombre = nombre
	def QueNombre(self):
		return self.nombre
	def Join(self):
		self.join() 
#---------------------------PING TO MAINTAIN CONNECTIONS WITH DB--------------------------------------------------------
def PingServer():
	global tab1,  logger
	try:
		for i1 in range(tab1.size): #does ping for the complete pool of connections
			ping1 = tab1.connpool[i1].ping(reconnect=True, attempts=3, delay=1) #reconnect in case of lost connection
			if  ping1 !=  None:
				break
		#de esta forma, si no hay nadie conectandose, la conexion seguiria activa, mediante este ping.
		#si se desconectara, y no pudieramos volver a conectarnos, este proceso está dentro de un bucle hecho en shell que le obliga a volver a ejecutarse 
		if  ping1 ==  None:
			px = "Conectado"
	except:
		for i1 in range(tab1.size):
			tab1.connpool[i1].reconnect(attempts=2, delay=1)
		px = "Desconnected, trying to reconnect"
		logger.info("Ping Server : {} {}".format(ChimoFunc18.ahora(),  px))
		#exit()		
	#logger.info("Ping Servidor : {} {}".format(ChimoFunc18.ahora(),  px))
	timerping=threading.Timer(1000, PingServer)
	timerping.start()	
#----------------------------------------------------------------------------------------------------------------------

eventlet.monkey_patch(select=False) #puesto select=False, porque con la version 3.6.4 da error de poll en modulo select
app = Flask(__name__)
my1=Myconfig.claves()
#----------------------------------------------------------------------------------------------------------------------
LevelDebug = "I"
dirlog='./Log/'
fichlog= "{}gastos".format(dirlog)
logger = logging.getLogger(__name__)
if LevelDebug == "D":
	Info_Debug = logging.DEBUG
else:
	Info_Debug = logging.INFO
logger.setLevel(Info_Debug)
filelogh = logging.handlers.TimedRotatingFileHandler(filename=fichlog+'.log', when='D', interval=2,  backupCount=4,  utc=True)
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s',  datefmt='%d-%m-%y %H:%M:%S')
filelogh.setFormatter(formatter)
logger.addHandler(filelogh)
logger.info('Start Logging to Server')
#app.logger.addHandler(filelogh)
#----------------------------------------------------------------------------------------------------------------------
my1=Myconfig.claves()
datos_user = my1.user_gastos()
DictConServer={}
numuser=0
numensaje = 0
miconfig={}
python_exe = "python{}{}".format(sys.version_info.major,  sys.version_info.minor)
bd = datos_user.get("bd")
user = datos_user.get('usuario')
pwd = datos_user.get('password')
server = datos_user.get('host')
miconfig.setdefault('bd', bd)

miconfig.setdefault('userdb', user)
miconfig.setdefault('pwddb', pwd)
miconfig.setdefault('numuser', numuser)
miconfig.setdefault('log', logger)
miconfig.setdefault('nmens', numensaje)
miconfig.setdefault('Server', my1.ipaddr)
miconfig.setdefault('NomServer', my1.nombrepc)
ndel = 0
#tab1 = MyFuncPool18.DicciDatos_MyPool(bd, user, pwd,  server)
tab1 = MyFuncPool18.DicciDatos_MyPool("uiaudvqu_berentec", "uiaudvqu_joaquin", "Benidorm18",  "host46.hostinet.com")
if tab1 == None:
	logger.info("Error de Conexion MySQL")
	exit()
miconfig.setdefault('mysql', tab1)
#una forma de generar un numero random, puede ser os.urandom de los bytes que queramos
num_secreto=os.urandom(32) #genera una clave aleatoria cada vez de 32 bytes
app.secret_key = num_secreto#secret key para la sesion, de forma que una sesion no pueda ser cambiada por el browser
miconfig.setdefault('arranque', ChimoFunc18.timestamp(1))
Usuarios={}
miconfig.setdefault("Usuarios", Usuarios)
Mensajes = MyFuncPool18.BerMessages(tab1)
miconfig.setdefault("Mensajes", Mensajes)
timerping=threading.Timer(50, PingServer) #to maintain connection, when inactivity
timerping.start()

@app.route('/hola/')
@app.route('/hola/<name>') #los dos router van a la misma funcion, y le pasan el argumento ya sea None o el nombre, la pagina html, decide que hacer con el argumento, se hace con jinja2
def hello(name=None):
	if  name == "joaquin":
		try:
			pp = tab1.conn.ping() #para evitar que el servidor, desconecte esta conexion por inactividad del cliente, por el parametro wait_timeout
			#de esta forma, si no hay nadie conectandose, la conexion seguiria activa, mediante este ping.
			#si se desconectara, y no pudieramos volver a conectarnos, este proceso está dentro de un bucle hecho en shell que le obliga a volver a ejecutarse 
			if  pp ==  None:
				px = "Conectado"
		except:
			px = "Desconectado, saliendo para volver a Ejecutar"
			logger.info("Ping Servidor : {} {}".format(ChimoFunc18.ahora(),  px))
			exit()		
		logger.info("Ping Servidor : {} {}".format(ChimoFunc18.ahora(),  px))
		return px
	else:
		return render_template('hola.html', name=name)
@app.route('/server/<name>')
def servidor(name="ws_time"):
	return render_template(name+'.html')
@app.route('/user/<username>') #es como si nos pasara un parametro, ejecuta siempre la funcion,
def show_user_profile(username):
	# show the user profile for that user
	return 'User %s' % username
@app.route('/post/<int:post_id>') #aqui obliga a recibir un entero, si se pasa un string da un error de pagina no encontrada
def show_post(post_id):
	# show the post with the given id, the id is an integer
	return 'Post %d' % post_id
@app.route('/projects/') #funciona en cualquier caso, tanto si se pasa / del final como si no
def projects():
	return 'The project page'

@app.route('/about') #funciona solo se se pasa sin / del final
def about():
	return FuncFormMariaDb.About('get', session.get('user'), request.environ, miconfig)	
@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
	global numuser, DictConServer, miconfig
	#if 'user' in session and request.method == 'GET':
	#	return 'Logged in as %s' % escape(session['user'])
	if 'user' in session:
		return FuncFormMariaDb.Menu(miconfig, numuser, session['user'])
	error = None
	if request.method == 'POST':
		usr1 = request.form['user']
		pwd1 = request.form['password']
		valido1, idioma = FuncFormMariaDb.valid_login(miconfig, usr1, pwd1)
		if valido1 != False:
			#numuser = valido1
			miconfig.setdefault("coduser",  str(valido1))		
			session['user'] = request.form['user']
			numuser+=1
			#logger.info(request)
			logger.info("Login de : "+session.get('user'))
			valores={'ultima_conexion':ChimoFunc18.timestamp(1), 'nombre':session.get('user')}
			tab1.ActFila('usuario', valores)
			Fechas = ChimoFunc18.Fechas(tab1, idioma)
			miconfig.get("Usuarios").setdefault(session.get('user'),  {"idioma": idioma, "coduser": str(valido1), "numuser": numuser, "fechas": Fechas})
			return FuncFormMariaDb.Menu(miconfig, numuser, request.form['user'])
		else:
			error = 'Invalid username/password'
	return render_template('login.html', fecha=ChimoFunc18.fechahoy(), error=error) #cuando sea GET

@app.route('/upload', methods=['GET', 'POST']) #poner enctype="multipart/form-data" en el fichero html
def upload_file():
	if request.method == 'POST':
		f = request.files['the_file']
		f.save('/uploads/' + secure_filename(f.filename)) #f.save('/var/www/uploads/uploaded_file.txt')
@app.route('/mensaje')
def mensaje():
	return render_template('pymensajes2.html')
@app.errorhandler(404)
def page_not_found(error):
	return render_template('page_not_found.html')
@app.route('/logout')
@app.route('/salir')
@app.route('/menu/salir')
def logout():
	global numuser, DictConServer, miconfig
	# remove the username from the session if it's there
	if session.get('user'):
		miconfig.get("Usuarios").pop(session.get('user'))
		logger.info("Logout de : "+session.get('user'))
		miconfig.pop("coduser")
		session.pop('user')
	return render_template('login.html', fecha=ChimoFunc18.fechahoy())

@app.route('/modulos', methods=['POST', 'GET'])
def modulos():
	global DictConServer, miconfig
	error = None
	if request.method == 'POST':
		#se ha rellenado el form y venimos aqui ejecutar lo que venga del form
		return FuncFormMariaDb.ModulosCon('post', DictConServer,  session.get('user'), logger)
	#se debe rellenar el form
	else:
		return FuncFormMariaDb.ModulosCon('get', DictConServer,  session.get('user'), logger)
#si recibimos /funcion, es queremos ejecutar una funcion
#aqui venimos para todas las opciones del menu
@app.route('/menu/Form_Generico/<opcion>', methods=['POST', 'GET'])
def FormGen(opcion):
	if request.method == 'POST':
		#se ha rellenado el form y venimos aqui ejecutar lo que venga del form
		return FuncFormMariaDb.Form_Generico('post', numuser, session.get('user'), opcion, request.environ, miconfig,  request.form)
	#se debe rellenar el form
	else:
		params= request.environ.get("QUERY_STRING")
		if  params == "" or  params ==  None:
			params =  None
		return FuncFormMariaDb.Form_Generico('get', numuser, session.get('user'), opcion, request.environ, miconfig,  params)
#ejecuta un proceso del sistema operativo con salida a un fichero del resultado, y despues se muestra el resultado usando mensajes.html
@app.route('/menu/Proceso/<opcion>', methods=['POST', 'GET'])
def Proceso(opcion):
	global miconfig
	return FuncFormMariaDb.EjecProceso(opcion, miconfig, session.get('user'), dirlog,  python_exe)

@app.route('/menu/<opcion>', methods=['POST', 'GET'])
def funcion(opcion):
	global DictConServer, miconfig
	error = None
	assert opcion
	if 'user' not in session:
		return render_template('login.html', fecha=ChimoFunc18.fechahoy(), error=error)
	if request.method == 'POST':
		#se ha rellenado el form y venimos aqui ejecutar lo que venga del form
		return getattr(FuncFormMariaDb, opcion)('post', numuser, session.get('user'), opcion, request.environ, miconfig)
	#se debe rellenar el form
	else:
		return getattr(FuncFormMariaDb, opcion)('get', numuser, session.get('user'), opcion, request.environ, miconfig)
#si recibimos /funcion, es queremos ejecutar una funcion
@app.route('/funcion/<funcion>', methods=['POST', 'GET'])
def ejecuta(funcion):
	global miconfig
	nc, datos = ChimoFunc18.extrae2(funcion, "-")
	if  nc == 1:
		func1 = datos[0]
		params = ""
	else:
		func1=datos[0]
		params=datos[1]
	return getattr(FuncFormMariaDb, func1)(request.method, params, request.environ, miconfig)
#todo lo que venga de un movil se manda a una aplicación diferente
@app.route('/mobile/<opcion>')
def MobApp(opcion):
	assert opcion


if __name__ == '__main__':
	#socketio.run(app, host='0.0.0.0', port=10825)#, log_output=True) #arranca en el 5000
	app.run(host='0.0.0.0', port=my1.puerto_hostinet_gastos, debug=False) #para que pueda accederse desde cualquier IP, y que recargue el programa cuando cambiemos el contenido : debug=True
