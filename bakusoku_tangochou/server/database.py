from sqlite3 import connect, Connection
from os import remove
from os.path import exists, isdir
from shutil import rmtree
from abc import ABC, abstractmethod
from os import urandom
from typing import Iterable
from hashlib import sha3_256

from ..core.util import ask_yes_no
from ..core import Question,Level,Record, Difficulty,User,RankingEntry, UserData

class Database(ABC):
	@abstractmethod
	def add_question(self,question:Question):
		pass
	def add_questions(self,questions:Iterable[Question]):
		for i in questions:
			self.add_question(i)
	@abstractmethod
	def get_random_questions(self,level:Level,num:int)->list[Question]:
		pass
	@abstractmethod
	def add_record(self,record:Record):
		pass
	@abstractmethod
	def get_rank(self,difficulty:Difficulty,user_name:str)->int:
		pass
	@abstractmethod
	def get_ranking(self,difficulty:Difficulty,start:int,end:int)->Iterable[RankingEntry]:
		pass
	@abstractmethod
	def _add_user(self,user:User):
		pass
	def add_user(self,user_data:UserData)->bool:
		if self._get_user(user_data.name):
			return False
		salt = urandom(32)
		hash_ = sha3_256(salt+(user_data.name+":"+user_data.password).encode())
		self._add_user(User(user_data.name,salt,hash_.digest()))
		return True
	@abstractmethod
	def _get_user(self,name:str)->User|None:
		pass
	def check_user(self,user_data:UserData):
		user = self._get_user(user_data.name)
		return user is not None and user.hash == sha3_256(user.salt+(user_data.name+":"+user_data.password).encode()).digest()
	def __enter__(self):
		return self
	@abstractmethod
	def __exit__(self,ex_type,ex_value,trace):
		pass
LEVELS = ["beginner","intermediate","advanced"]
DIFFICULTIES = ["easy","normal","hard","extreme"]
class _SqliteDatabase(Database):
	def __init__(self, con:Connection):
		super().__init__()
		self.con=con
		self.cur=con.cursor()
	def init(self):
		self.cur.execute("""
CREATE TABLE IF NOT EXISTS users (
	name TEXT PRIMARY KEY NOT NULL,
	salt BINARY(32) NOT NULL,
	hash BINARY(32) NOT NULL
)
""")
		self.cur.execute("""
CREATE TABLE IF NOT EXISTS questions (
	id SERIAL PRIMARY KEY,
	category TEXT NOT NULL,
	subcategory TEXT NOT NULL,
	keyword TEXT NOT NULL,
	level TINYINT UNSIGNED NOT NULL,
	sentence TEXT NOT NULL,
	japanese_translation TEXT NOT NULL
)
""")
		self.cur.execute("""
CREATE TABLE IF NOT EXISTS records (
	id SERIAL PRIMARY KEY,
	user_name TEXT NOT NULL,
	difficulty TINYINT UNSIGNED NOT NULL,
	score INTEGER UNSIGNED NOT NULL,
	time_in_ns BIGINT UNSIGNED NOT NULL
)
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS beginner_questions AS SELECT * FROM questions WHERE level = 0
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS intermediate_questions AS SELECT * FROM questions WHERE level = 1
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS advanced_questions AS SELECT * FROM questions WHERE level = 2
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS easy_tops AS SELECT RANK() OVER (order by score DESC, time_in_ns ASC) rank,user_name,score,time_in_ns,row_number() over (order by score DESC, time_in_ns ASC) rownum FROM (
	select *,
	row_number() over (partition by user_name order by score DESC, time_in_ns ASC) rownum
	from records WHERE difficulty = 0
) where rownum = 1 order by score DESC, time_in_ns ASC
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS normal_tops AS SELECT RANK() OVER (order by score DESC, time_in_ns ASC) rank,user_name,score,time_in_ns,row_number() over (order by score DESC, time_in_ns ASC) rownum FROM (
	select *,
	row_number() over (partition by user_name order by score DESC, time_in_ns ASC) rownum
	from records WHERE difficulty = 1
) where rownum = 1 order by score DESC, time_in_ns ASC
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS hard_tops AS SELECT RANK() OVER (order by score DESC, time_in_ns ASC) rank,user_name,score,time_in_ns,row_number() over (order by score DESC, time_in_ns ASC) rownum FROM (
	select *,
	row_number() over (partition by user_name order by score DESC, time_in_ns ASC) rownum
	from records WHERE difficulty = 2
) where rownum = 1 order by score DESC, time_in_ns ASC
""")
		self.cur.execute("""
CREATE VIEW IF NOT EXISTS extreme_tops AS SELECT RANK() OVER (order by score DESC, time_in_ns ASC) rank,user_name,score,time_in_ns,row_number() over (order by score DESC, time_in_ns ASC) rownum FROM (
	SELECT *,
	row_number() over (partition by user_name order by score DESC, time_in_ns ASC) rownum
	FROM records WHERE difficulty = 3
) where rownum = 1 order by score DESC, time_in_ns ASC
""")
		self.con.commit()
	def add_question(self,question:Question):
		self.cur.execute("""
INSERT INTO questions (category,subcategory,keyword,level,sentence,japanese_translation) VALUES(?,?,?,?,?,?)
""",question)
		self.con.commit()
	def add_questions(self,questions:Iterable[Question]):
		self.cur.executemany("""
INSERT INTO questions (category,subcategory,keyword,level,sentence,japanese_translation) VALUES(?,?,?,?,?,?)
""",questions)
		self.con.commit()
	def get_random_questions(self,level:Level,num:int)->list[Question]:
		tmp = LEVELS[level]
		assert tmp in LEVELS
		self.cur.execute(f"""
SELECT category,subcategory,keyword,level,sentence,japanese_translation FROM {tmp}_questions ORDER BY RANDOM() LIMIT ?
""",(num,))
		return [Question(*i) for i in self.cur.fetchall()]
	def add_record(self,record:Record):
		self.cur.execute("""
INSERT INTO records (user_name,difficulty,score,time_in_ns) VALUES(?,?,?,?)
""",record)
		self.con.commit()
	def get_rank(self,difficulty:Difficulty,user_name:str)->int:
		tmp = DIFFICULTIES[difficulty]
		assert tmp in DIFFICULTIES
		self.cur.execute(f"""
SELECT rank FROM {tmp}_tops WHERE user_name=? LIMIT 1
""",(user_name,))
		return self.cur.fetchall()[0][0]
	def get_ranking(self,difficulty:Difficulty,start:int,end:int)->Iterable[RankingEntry]:
		tmp = DIFFICULTIES[difficulty]
		assert tmp in DIFFICULTIES
		self.cur.execute(f"""
SELECT rank,user_name,score,time_in_ns FROM {tmp}_tops WHERE rownum >= ? AND rownum <= ?
""",(start+1,end))
		return [RankingEntry(*i) for i in self.cur.fetchall()]
	def _add_user(self,user:User):
		self.cur.execute("""
INSERT INTO users VALUES(?,?,?)
""",user)
		self.con.commit()
	def _get_user(self,name:str)->User|None:
		self.cur.execute("""
SELECT * FROM users WHERE name=? LIMIT 1
""",(name,))
		tmp=self.cur.fetchall()
		return User(*tmp[0]) if tmp else None
	def __exit__(self,ex_type,ex_value,trace):
		self.con.close()


def create_database(path:str, continue_if_exist:bool|None=None)->Database:
	if exists(path):
		if continue_if_exist is None:
			print(f"「{path}」にはすでにデータが存在します。")
			if not (continue_if_exist:=ask_yes_no("置換しますか","置換する","置換せず、プログラムを終了する")):
				raise SystemExit()
		if not continue_if_exist:
			raise FileExistsError(f"「{path}」には既にデータが存在しました。")
		if isdir(path):
			rmtree(path)
		else:
			remove(path)
	db=_SqliteDatabase(connect(path))
	db.init()
	return db
def load_database(path:str, create_if_not_exist:bool|None=None)->Database:
	if not exists(path):
		if create_if_not_exist is None:
			print(f"「{path}」というファイルは存在しません。")
			if not (create_if_not_exist:=ask_yes_no("新たに作成しますか","置換する","置換せず、プログラムを終了する")):
				raise SystemExit()
		if not create_if_not_exist:
			raise FileNotFoundError(f"「{path}」というファイルは存在しませんでした。")
	db=_SqliteDatabase(connect(path))
	return db