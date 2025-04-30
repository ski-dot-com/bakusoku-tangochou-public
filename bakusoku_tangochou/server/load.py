from csv import reader

from ..core import Question,Level
from .database import create_database

def load_csv(csv_path:str,database_path:str="default.db",continue_if_exist:bool|None=None):
	print(f"「{csv_path}」から例文データを読み込み、「{database_path}」に新たにデータベースを作成しています…")
	with open(csv_path,encoding="utf8")as csv, create_database(database_path,continue_if_exist) as db:
		db.add_questions(Question(cat,sub,key,Level[lev.capitalize()],stc.replace("[","{").replace("]","}"),jtr)for cat,sub,key,lev,stc,jtr in reader(csv))
