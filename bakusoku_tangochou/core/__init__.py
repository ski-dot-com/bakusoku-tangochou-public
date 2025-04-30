from __future__ import annotations
from typing import NamedTuple
from enum import IntEnum, StrEnum

class Level(IntEnum):
	Beginner=0
	Intermediate=1
	Advanced=2
	def __repr__(self):
		return f"Level.{self.name}"
class Difficulty(IntEnum):
	# かんたん
	Easy=0
	# ふつう
	Normal=1
	# むずかしい
	Hard=2
	# 激ムズ
	Extreme=3
	def __repr__(self):
		return f"Difficulty.{self.name}"
	@classmethod
	def from_json(cls, data):
		difficulty = data
		if isinstance(difficulty,str):
			try:
				return Difficulty[difficulty]
			except KeyError:
				raise TypeError()
		elif isinstance(difficulty,list):
			if len(difficulty)!=5 or any(not isinstance(i,int)for i in difficulty):
				raise TypeError()
			return CustomDifficulty(*difficulty)
		else:
			raise TypeError()
	def to_json(self):
		return self.name
class CustomDifficulty(NamedTuple):
	easy_num:int
	normal_num:int
	hard_num:int
	show_level:int
	level_strategy:int
	@classmethod
	def from_json(cls, data):
		difficulty = data
		if isinstance(difficulty,str):
			try:
				return Difficulty[difficulty]
			except KeyError:
				raise TypeError()
		elif isinstance(difficulty,list):
			if len(difficulty)!=5 or any(not isinstance(i,int)for i in difficulty):
				raise TypeError()
			return CustomDifficulty(*difficulty)
		else:
			raise TypeError()
	def to_json(self):
		return [*self]
class UserData(NamedTuple):
	name:str
	password:str
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,list) or len(data)!=2 or any(not isinstance(i,str)for i in data):
			raise TypeError()
		return UserData(*data)
	def to_json(self):
		return[*self]
class Question(NamedTuple):
	category:str
	subcategory:str
	keyword:str
	level:Level
	sentence:str
	japanese_translation:str
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,list) or len(data)!=6 or any(not isinstance(data[i],int if i==3 else str)for i in range(6)):
			raise TypeError()
		data[3]=Level(data[3])
		return Question(*data)
	def to_json(self):
		res:list=[*self]
		res[3]=int(res[3])
		return res
class Record(NamedTuple):
	user_name:str
	difficulty:Difficulty
	score:int
	time_in_ns:int
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,list) or len(data)!=4 or any(not isinstance(data[i],[str,int,int,int][i])for i in range(4)):
			raise TypeError()
		data[1]=Difficulty(data[1])
		return Record(*data)
	def to_json(self):
		res:list=[*self]
		res[1]=int(res[1])
		return res
class RankingEntry(NamedTuple):
	rank:int
	user_name:str
	score:int
	time_in_ns:int
	@classmethod
	def from_json(cls, data):
		if not isinstance(data,list) or len(data)!=4 or any(not isinstance(data[i],[int,str,int,int][i])for i in range(4)):
			raise TypeError()
		return RankingEntry(*data)
	def to_json(self):
		return[*self]
class User(NamedTuple):
	name:str
	salt:bytes
	hash:bytes
DIF2NUMS={
	Difficulty.Easy:[9,1,0,2,0],
	Difficulty.Normal:[5,13,2,2,0],
	Difficulty.Hard:[0,10,15,1,0],
	Difficulty.Extreme:[0,0,25,0,0]
}
SHOW_LEVELS=["なし","大分類","大分類と小分類","大分類と小分類、そしてキーワード(ほぼ回答)"]
DIFFICULTY_STRATEGIES=["優しい順","ミックスして表示","ミックスして非表示"]
DIFFICULTY_NAMES=[
	"かんたん",
	"ふつう",
	"むずかしい",
	"激ムズ",
]
LEVEL_NAMES=[
	"初級",
	"中級",
	"上級",
]
TIME_CONST_FACTOR=5000000000
TIME_PROPO_FACTOR=400000000