from http.server import HTTPServer, BaseHTTPRequestHandler
from ssl import SSLContext, PROTOCOL_TLS_SERVER
from typing import NamedTuple
from uuid import uuid4, UUID
from os.path import exists
from time import monotonic_ns
from datetime import datetime
from random import shuffle
from jsonrpcserver import method, dispatch, Result, Success, Error, InvalidParams

from ..core import UserData,Difficulty,CustomDifficulty,DIF2NUMS,Level,Question,Record
from .database import load_database,Database

def serve(database_path:str="default.db",cert_path:str="cert.pem",key_path:str="key.pem",port:int=8080):
	with load_database(database_path,False) as db:
		context = SSLContext(PROTOCOL_TLS_SERVER)
		context.load_cert_chain(cert_path,key_path)
		if not exists(cert_path):
			print("Error: 証明書ファイルが存在しませんでした。サブコマンド「generate_cert」を用いると秘密鍵と一緒に生成できます。")
			return
		if not exists(key_path):
			print("Error: 秘密鍵ファイルが存在しませんでした。サブコマンド「generate_cert」を用いると生成できます。")
			return
		class HTTPHandler(BaseHTTPRequestHandler):
			def do_POST(self):
				req=self.rfile.read(int(self.headers["Content-Length"])).decode()
				res=dispatch(req,context=db)
				self.send_response(200 if res else 204)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				self.wfile.write(res.encode())
				print(f"{datetime.now().isoformat()}: {req}->{res}")
		try:
			with HTTPServer(("localhost",port), HTTPHandler) as server:
				server.socket=context.wrap_socket(server.socket, server_side=True)
				print(f"サーバーが起動しました。\nこのサーバーのローカルでのURL: https://localhost:{port}/")
				server.serve_forever()
		except KeyboardInterrupt:
			print("サーバーが終了しました。")

class SessionData(NamedTuple):
	user_name:str
	expired_at:int
class TryData(NamedTuple):
	session_id:UUID
	difficulty:Difficulty|CustomDifficulty
	questions:list[Question]
sessions:dict[UUID,SessionData]={}
tries:dict[UUID,TryData]={}
@method
def signup(db:Database,/,user_data)->Result:
	try:
		user_data=UserData.from_json(user_data)
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if not db.add_user(user_data):
		return Error(-1,"同じ名前のユーザーが既に存在します。")
	while (uuid:=uuid4())in sessions and not sessions[uuid].expired_at<monotonic_ns():pass
	sessions[uuid]=SessionData(user_data.name,monotonic_ns()+3600000000000)
	return Success(uuid.hex)
@method
def login(db:Database,/,user_data)->Result:
	try:
		user_data=UserData.from_json(user_data)
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if not db.check_user(user_data):
		return Error(0, "認証に失敗しました: ユーザー名かパスワードが異なります。再度確認してください。")
	while (uuid:=uuid4())in sessions and not sessions[uuid].expired_at<monotonic_ns():pass
	sessions[uuid]=SessionData(user_data.name,monotonic_ns()+3600000000000)
	return Success(uuid.hex)
def hide_category(question:Question,show_level:int):
	tmp = [*question]
	tmp[show_level:3]=[""]*(3-show_level)
	return Question(*tmp) # type: ignore
	
@method
def start_try(db:Database,/,session_id,difficulty)->Result:
	try:
		difficulty=Difficulty.from_json(difficulty)
		if not isinstance(session_id,str):
			raise TypeError
		try:
			session_id=UUID(hex=session_id)
		except ValueError:
			raise TypeError
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if session_id not in sessions or sessions[session_id].expired_at<monotonic_ns():
		if session_id in sessions:
			del sessions[session_id]
		return Error(1, "認証に失敗しました: 指定されたセッションは存在しないか期限切れです。")
	match difficulty:
		case Difficulty(d):
			data=CustomDifficulty(*DIF2NUMS[d])
		case CustomDifficulty() as data:
			pass
	res=sum((db.get_random_questions(i,n)for i,n in [[Level.Beginner,data.easy_num],[Level.Intermediate,data.normal_num],[Level.Advanced,data.hard_num]]),start=[])
	if data.level_strategy != 0:
		shuffle(res)
		if data.level_strategy == 2:
			res=[Question(c,s,k,Level.Intermediate,st,j)for c,s,k,_,st,j in res]
	res=[hide_category(i,data.show_level)for i in res]
	while (uuid:=uuid4())in tries and not sessions[tries[uuid].session_id].expired_at<monotonic_ns():pass
	tries[uuid]=TryData(session_id, difficulty,res)
	sessions[session_id]=SessionData(sessions[session_id].user_name, max(sessions[session_id].expired_at,monotonic_ns()+3600000000000))
	return Success(uuid.hex)
@method
def get_questions(_:Database,/,try_id)->Result:
	try:
		if not isinstance(try_id,str):
			raise TypeError
		try:
			try_id=UUID(hex=try_id)
		except ValueError:
			raise TypeError
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if try_id not in tries or tries[try_id].session_id not in sessions or sessions[tries[try_id].session_id].expired_at<monotonic_ns():
		if try_id in tries:
			if tries[try_id].session_id in sessions:
				del sessions[tries[try_id].session_id]
			del tries[try_id]
		return Error(2, "認証に失敗しました: 指定されたトライは存在しないか期限切れです。")
	return Success([i.to_json()for i in tries[try_id].questions])
@method
def end_try(db:Database,/,try_id,score,time_in_ns)->Result:
	try:
		if not isinstance(try_id,str):
			raise TypeError
		try:
			try_id=UUID(hex=try_id)
		except ValueError:
			raise TypeError
		if try_id not in tries or tries[try_id].session_id not in sessions or sessions[tries[try_id].session_id].expired_at<monotonic_ns():
			if try_id in tries:
				if tries[try_id].session_id in sessions:
					del sessions[tries[try_id].session_id]
				del tries[try_id]
			return Error(2, "認証に失敗しました: 指定されたトライは存在しないか期限切れです。")
		dif=tries[try_id].difficulty
		if isinstance(dif,Difficulty):
			record=Record.from_json([sessions[tries[try_id].session_id].user_name,int(dif),score,time_in_ns])
			db.add_record(record)
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	
	del tries[try_id]
	return Success()
@method
def get_rank(db:Database,/,session_id,difficulty)->Result:
	try:
		difficulty=Difficulty.from_json(difficulty)
		if not isinstance(difficulty,Difficulty):
			raise TypeError
		if not isinstance(session_id,str):
			raise TypeError
		try:
			session_id=UUID(hex=session_id)
		except ValueError:
			raise TypeError
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if session_id not in sessions or sessions[session_id].expired_at<monotonic_ns():
		if session_id in sessions:
			del sessions[session_id]
		return Error(1, "認証に失敗しました: 指定されたセッションは存在しないか期限切れです。")
	return Success(db.get_rank(difficulty, sessions[session_id].user_name))
@method
def get_ranking(db:Database,/,session_id,difficulty,start,end)->Result:
	try:
		difficulty=Difficulty.from_json(difficulty)
		if not isinstance(difficulty,Difficulty):
			raise TypeError
		if not isinstance(session_id,str):
			raise TypeError
		if not all(isinstance(i,int)for i in (start,end)):
			raise TypeError
		try:
			session_id=UUID(hex=session_id)
		except ValueError:
			raise TypeError
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if session_id not in sessions or sessions[session_id].expired_at<monotonic_ns():
		if session_id in sessions:
			del sessions[session_id]
		return Error(1, "認証に失敗しました: 指定されたセッションは存在しないか期限切れです。")
	return Success([i.to_json()for i in db.get_ranking(difficulty, start,end)])
@method
def logout(_:Database,/,session_id)->Result:
	try:
		if not isinstance(session_id,str):
			raise TypeError
		try:
			session_id=UUID(hex=session_id)
		except ValueError:
			raise TypeError
	except TypeError:
		return InvalidParams("引数の型が適当でありません。")
	if session_id not in sessions or sessions[session_id].expired_at<monotonic_ns():
		if session_id in sessions:
			del sessions[session_id]
		return Error(1, "認証に失敗しました: 指定されたセッションは存在しないか期限切れです。")
	del sessions[session_id]
	return Success()