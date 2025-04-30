
from ..core import Difficulty, DIFFICULTY_NAMES
from .menu_graphic import getch
from .session import Session

RANKING_ENTRIES=10

def show_ranking(session:Session):
	difficulty:Difficulty=Difficulty.Easy
	pos=0
	while True:
		print(f"\x1b[2J\x1b[1;1fランキング({DIFFICULTY_NAMES[difficulty]}) (↑/↓:表示範囲を移動, ←/→:難易度を変更, s:指定した場所に移動, q:メニューに戻る):")
		ranking=session.get_ranking(difficulty, pos, pos+11)
		if ranking is None:
			for _ in range(100):
				if session.relogin():
					break
			else:
				print("タイムアウト等により、自動的にログアウトされました。")
				print("繰り返し再ログインに失敗したため、再ログインを諦めます。")
				return False
			continue
		l = len(ranking)
		last = l!=11
		print(f"{l=}, {last=}")
		if l:
			max_rank_width=max(len(str(i.rank))for i in ranking[:10])
			for i in ranking[:10]:
				rank=str(i.rank).ljust(max_rank_width)
				print(f"{rank}位:{i.user_name} ({i.score}点, {i.time_in_ns/1000000000}秒)")
		else:
			print("----(該当なし)----")
		match getch():
			case b"s":
				i=input("表示枠の一番上の順位: ")
				try:
					pos=int(i)
				except ValueError:
					pass
			case b"\xe0":
				match getch():
					case b"H":
						if pos != 0:
							pos-=1
					case b"P":
						if not last:
							pos+=1
					case b"M":
						difficulty=Difficulty((difficulty+1)%4)
						pos=0
					case b"K":
						difficulty=Difficulty((difficulty-1)%4)
						pos=0
			case b"\x1b":
				if getch()==b"[":
					match getch():
						case b"A":
							if pos != 0:
								pos-=1
						case b"B":
							if not last:
								pos+=1
						case b"C":
							difficulty=Difficulty((difficulty+1)%4)
							pos=0
						case b"D":
							difficulty=Difficulty((difficulty-1)%4)
							pos=0
			case b"q":
				return True