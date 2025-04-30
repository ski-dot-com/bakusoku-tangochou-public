from __future__ import annotations
from json import load,dump
from sys import argv
from os import remove
from os.path import join,dirname,exists
from typing import NamedTuple

from ..core import Difficulty, CustomDifficulty, UserData
from ..core.util import ask_yes_no

class Config:
	def __init__(self,difficulty:Difficulty|CustomDifficulty, login_datas:list[LoginData]) -> None:
		self.difficulty=difficulty
		self.login_datas=login_datas
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,dict):
			raise TypeError()
		difficulty = data["difficulty"]
		login_datas = data["login_datas"]
		if not isinstance(login_datas,list):
			raise TypeError()
		return Config(Difficulty.from_json(difficulty),[LoginData.from_json(i)for i in login_datas])
	def to_json(self):
		return{"difficulty":self.difficulty.to_json(),"login_datas":[i.to_json()for i in self.login_datas]}
class LoginData(NamedTuple):
	server_url:str
	user_data:UserData
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,list) or len(data)!=3 or any(not isinstance(i,str)for i in data):
			raise TypeError()
		return LoginData(data[0],UserData(*data[1:]))
	def to_json(self):
		return[self.server_url,*self.user_data]
CONFIG_PATH=join(dirname(argv[0]),"config.json")
config:Config
def load_config():
	global config
	if exists(CONFIG_PATH):
		try:
			with open(CONFIG_PATH) as f:
				tmp = load(f)
			config=Config.from_json(tmp)
			return
		except Exception:
			print("設定の読み込みに失敗しました。プログラムの続行には既存の設定ファイルを削除し、再生成することが必要です。")
			if not ask_yes_no("再生成しますか","再生成する","再生成せず、プログラムを終了する"):
				raise SystemExit()
			remove(CONFIG_PATH)
	config=Config(Difficulty.Normal,[])
	save_config()
def save_config():
	with open(CONFIG_PATH,"w") as f:
		dump(config.to_json(),f)
load_config()