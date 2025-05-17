from __future__ import annotations
from jsonrpcclient import request, Ok, Error, parse
from uuid import UUID
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse
from ssl import PROTOCOL_TLSv1_2, _create_unverified_context
from json import dumps, loads
import urllib.request


from ..core import Difficulty, CustomDifficulty, Question, RankingEntry
from .config import LoginData

CTX=_create_unverified_context()
def post(url:str,json):
	with urllib.request.urlopen(urllib.request.Request(
		url,
		dumps(json).encode(),
		{
			"Content-Type": "application/json"
		}
	), context=CTX) as res:
		return loads(res.read())

class Session:
	def __init__(self,login_data:LoginData,session_id:UUID) -> None:
		self.server_url=login_data.server_url
		self.user_data=login_data.user_data
		self.session_id=session_id
		self.try_id=None
	@classmethod
	def signup(cls,login_data:LoginData)->Session|None:
		match parse(post(login_data.server_url,json=request("signup",(login_data.user_data.to_json(),)))):
			case Error(code) as err:
				if code == -1:
					return None
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,str):
					raise TypeError
				return Session(login_data, UUID(hex=res))
			case _:
				raise IOError()
	@classmethod
	def login(cls,login_data:LoginData)->Session|None:
		match parse(post(login_data.server_url,json=request("login",(login_data.user_data.to_json(),)))):
			case Error(code) as err:
				if code == 0:
					return None
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,str):
					raise TypeError
				return Session(login_data, UUID(hex=res))
			case _:
				raise IOError()
	def relogin(self)->bool:
		if self.session_id is not None:
			self.logout()
		match parse(post(self.server_url,json=request("login",(self.user_data.to_json(),)))):
			case Error(code) as err:
				if code == 0:
					return False
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,str):
					raise TypeError
				self.session_id=UUID(hex=res)
				return True
			case _:
				raise IOError()
	def get_questions(self,difficulty:Difficulty|CustomDifficulty)->list[Question]|None:
		if self.session_id is None:
			return None
		match parse(post(self.server_url,json=request("start_try",(self.session_id.hex,difficulty.to_json())))):
			case Error(code) as err:
				if code == 1:
					self.session_id=None
					return None
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,str):
					raise TypeError
				self.try_id=UUID(hex=res)
				match parse(post(self.server_url,json=request("get_questions",(res,)))):
					case Error(code) as err:
						if code == 2:
							self.session_id=None
							return None
						else:
							raise IOError(err)
					case Ok(res):
						if not isinstance(res,list):
							raise TypeError
						return [Question.from_json(i)for i in res]
					case _:
						raise IOError()
			case _:
				raise IOError()
	def end_try(self,score:int,time_in_ns:int)->bool:
		if self.session_id is None or self.try_id is None:
			if self.try_id is not None:
				self.try_id=None
			return False
		match parse(post(self.server_url,json=request("end_try",(self.try_id.hex,score,time_in_ns)))):
			case Error(code) as err:
				if code == 2:
					self.try_id=None
					self.session_id=None
					return False
				else:
					raise IOError(err)
			case Ok():
				self.try_id=None
				return True
			case _:
				raise IOError()
	def get_rank(self,difficulty:Difficulty)->int|None:
		if self.session_id is None:
			return None
		match parse(post(self.server_url,json=request("get_rank",(self.session_id.hex,difficulty.to_json())))):
			case Error(code) as err:
				if code == 1:
					self.session_id=None
					return None
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,int):
					raise TypeError()
				return res
			case _:
				raise IOError()
	def get_ranking(self,difficulty:Difficulty,start:int,end:int)->list[RankingEntry]|None:
		if self.session_id is None:
			return None
		match parse(post(self.server_url,json=request("get_ranking",(self.session_id.hex,difficulty.to_json(),start,end)))):
			case Error(code) as err:
				if code == 1:
					self.session_id=None
					return None
				else:
					raise IOError(err)
			case Ok(res):
				if not isinstance(res,list):
					raise TypeError()
				return [RankingEntry.from_json(i)for i in res]
			case _:
				raise IOError()
	def logout(self)->bool:
		if self.session_id is None:
			return False
		match parse(post(self.server_url,json=request("logout",(self.session_id.hex,)))):
			case Error(code) as err:
				if code == 1:
					self.session_id=None
					return False
				else:
					raise IOError(err)
			case Ok():
				self.session_id=None
				return True
			case _:
				raise IOError()
	def __enter__(self):
		return self
	def __exit__(self,ex_type,ex_value,trace):
		self.logout()