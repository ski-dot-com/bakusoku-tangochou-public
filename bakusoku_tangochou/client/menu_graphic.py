# import curses
import sys
from unicodedata import east_asian_width
from getpass import getpass
if sys.platform == "win32":
	from msvcrt import getch
else:
	import tty,termios
	def getchs():
		while True:
			fd=sys.stdin.fileno()
			old=termios.tcgetattr(fd)
			try:
				tty.setraw(fd)
				tmp=sys.stdin.read(1)
			finally:
				termios.tcsetattr(fd, termios.TCSADRAIN, old)
			for c in tmp.encode("shift-jis"):
				yield bytes([c])
	getchs_value=getchs()
	def getch():
		return next(getchs_value)

from ..core import DIF2NUMS, Difficulty, CustomDifficulty, SHOW_LEVELS, DIFFICULTY_STRATEGIES, UserData, DIFFICULTY_NAMES
from ..core.util import ask_yes_no
from .config import config, save_config, LoginData
from .session import Session

def select(title:str, options:list[str], default:int=0, value_on_q:int|None=None):
	# option_count=len(options)
	# print("\n"*option_count,end="")
	# try:
	#     window = curses.initscr()
	#     (y,x)=window.getyx()
	#     y-=len(options)
	#     curses.cbreak()
	#     curses.noecho()
	#     window.addstr(y,x,title, curses.A_BOLD)
	#     selection = default
	#     while True:
	#         for i,opt in enumerate(options):
	#             selected = selection==i
	#             window.addstr(y+1+i,x,f"({"*"if selected else " "}) ", curses.A_REVERSE if selected else curses.A_NORMAL)
	#             window.addstr(y+1+i,x+4,opt, curses.A_NORMAL)
	#         match window.getch():
	#             case curses.KEY_ENTER|Consts.ORD_SP:
	#                 return selection
	#             case curses.KEY_DOWN|Consts.ORD_TAB:
	#                 selected+=1
	#                 selected%=option_count
	#             case curses.KEY_UP:
	#                 selected-=1
	#                 selected%=option_count
	# finally:
	#     curses.endwin()
	option_count=len(options)
	print(title+":")
	selection = default
	while True:
		for i,opt in enumerate(options):
			selected = selection==i
			print(f"{"\x1b[7m(*)\x1b[m"if selected else "( )"} {opt}")
		sys.stdout.flush()
		match getch():
			case b"q":
				if value_on_q is not None:
					return value_on_q
			case b"\t":
				selection+=1
				selection%=option_count
			case b"\r"|b" ":
				return selection
			case b"\xe0":
				match getch():
					case b"H":
						selection-=1
						selection%=option_count
					case b"P":
						selection+=1
						selection%=option_count
			case b"\x1b":
				if getch()==b"[":
					match getch():
						case b"A":
							selection-=1
							selection%=option_count
						case b"B":
							selection+=1
							selection%=option_count
		print(f"\033[{option_count}F",end="")
MENU_COUNT=6
MENU_ITEM_NAMES=[
			"難易度　　　　　",
			"初級の問題の数　",
			"中級の問題の数　",
			"上級の問題の数　",
			"表示する分類　　",
			"レベルの取り扱い",
		]
MENU_ITEM_MAXS=[
			-1,
			-1,
			-1,
			3,
			2,
		]
def configure(dif: Difficulty | CustomDifficulty, quit_description:str="保存せずに終了"):
	menu_max_content_length=[0]*6
	max_title_len=0
	selected = 0
	while True:
		is_custom = isinstance(dif,CustomDifficulty)
		tmp=f"難易度設定(↑/↓:変更する項目を移動, タブ:変更する項目を一つ下に移動, {
			("スペース: カスタムモードをやめて、難易度を普通に変更"if is_custom else"←/→:変更, スペース:カスタムモードに変更") if selected == 0 else "←/-: 1減らす, →/+:1増やす, スペース: 直接編集" if selected<=3 else "←/→:変更"
		}, エンター:確定して保存, q:{quit_description}):"
		cur_title_len=sum(1 + (east_asian_width(i) in {"F","W","A"})for i in tmp)
		max_title_len=max(max_title_len,cur_title_len)
		print(tmp+" "*(max_title_len-cur_title_len+5))
		for i,opt in enumerate(MENU_ITEM_NAMES):
			is_selected = selected==i
			print(f"{"\x1b[7m(*)\x1b[m"if is_selected else "( )"} {opt}: ",end="")
			if i == 0:
				print(("  カスタム" if is_custom else f"< {DIFFICULTY_NAMES[dif]} >" if is_selected else DIFFICULTY_NAMES[dif])+"　　　　")
			else:
				value = (dif[i-1] if is_custom else DIF2NUMS[dif][i-1])
				if i==4:
					cur_c_len=len(SHOW_LEVELS[value])
					max_c_len=menu_max_content_length[3]=max(menu_max_content_length[3], cur_c_len)
					print((f"< {SHOW_LEVELS[value]} >" if is_selected else f"  {SHOW_LEVELS[value]}  ")+"　"*(max_c_len-cur_c_len))
				elif i==5:
					cur_c_len=len(DIFFICULTY_STRATEGIES[value])
					max_c_len=menu_max_content_length[4]=max(menu_max_content_length[4], cur_c_len)
					print((f"< {DIFFICULTY_STRATEGIES[value]} >" if is_selected else f"  {DIFFICULTY_STRATEGIES[value]}  ")+"　"*(max_c_len-cur_c_len))
				else:
					tmp=str(value)
					cur_c_len=len(tmp)
					max_c_len=menu_max_content_length[i-1]=max(menu_max_content_length[i-1], cur_c_len)
					print((f"- {tmp} +" if is_selected else f"  {tmp}  ")+" "*(max_c_len-cur_c_len))
					# print(f"{i-1}: {cur_c_len} -> {max_c_len}", file=sys.stderr)
			if i == 0 and not is_custom:
				print(end="\x1b[2m")
		print(end="\x1b[m")
		sys.stdout.flush()
		match getch():
			case b"\t":
				if is_custom:
					selected+=1
					selected%=MENU_COUNT
			case b" ":
				if not is_custom:
					dif=CustomDifficulty(*DIF2NUMS[dif])
				elif selected==0:
					dif=Difficulty.Normal
				elif selected<=3:
					print(f"\033[{MENU_COUNT-selected}F\x1b[7m(*)\x1b[m {MENU_ITEM_NAMES[selected]}: "+" "*(menu_max_content_length[selected-1]+4),end="\033[1G")
					tmp_=input(f"\x1b[7m(*)\x1b[m {MENU_ITEM_NAMES[selected]}:   ")
					try:
						tmp=[*dif]
						tmp__=tmp[selected-1]=int(tmp_)
						if tmp__ < 0:
							raise ValueError()
						tmp_=MENU_ITEM_MAXS[selected-1]
						if tmp_!=-1:
							tmp[selected-1]%=tmp_
						dif=CustomDifficulty(*tmp)
					except ValueError:
						pass
					print("\n"*(MENU_COUNT-1-selected),end="")
			case b"\r":
				return dif
			case b"\xe0":
				match getch():
					case b"H":
						if is_custom:
							selected-=1
							selected%=MENU_COUNT
					case b"P":
						if is_custom:
							selected+=1
							selected%=MENU_COUNT
					case b"M":
						if is_custom:
							if selected:
								tmp=[*dif]
								tmp[selected-1]+=1
								tmp_=MENU_ITEM_MAXS[selected-1]
								if tmp_!=-1:
									tmp[selected-1]%=tmp_
								dif=CustomDifficulty(*tmp)
						else:
							dif=Difficulty((dif+1)%4)
					case b"K":
						if is_custom:
							if selected:
								tmp=[*dif]
								tmp[selected-1]-=1
								tmp_=MENU_ITEM_MAXS[selected-1]
								if tmp_!=-1:
									tmp[selected-1]%=tmp_
								elif tmp[selected-1]==-1:
									tmp[selected-1]=0
								dif=CustomDifficulty(*tmp)
						else:
							dif=Difficulty((dif-1)%4)
			case b"\x1b":
				if getch()==b"[":
					match getch():
						case b"A":
							if is_custom:
								selected-=1
								selected%=MENU_COUNT
						case b"B":
							if is_custom:
								selected+=1
								selected%=MENU_COUNT
						case b"C":
							if is_custom:
								if selected:
									tmp=[*dif]
									tmp[selected-1]+=1
									tmp_=MENU_ITEM_MAXS[selected-1]
									if tmp_!=-1:
										tmp[selected-1]%=tmp_
									dif=CustomDifficulty(*tmp)
							else:
								dif=Difficulty((dif+1)%4)
						case b"D":
							if is_custom:
								if selected:
									tmp=[*dif]
									tmp[selected-1]-=1
									tmp_=MENU_ITEM_MAXS[selected-1]
									if tmp_!=-1:
										tmp[selected-1]%=tmp_
									elif tmp[selected-1]==-1:
										tmp[selected-1]=0
									dif=CustomDifficulty(*tmp)
							else:
								dif=Difficulty((dif-1)%4)
			case b"q":
				return
		print(f"\033[{MENU_COUNT+1}F",end="")
def login()->Session:
	option_count=len(config.login_datas)+1
	status=""
	selection = 0
	while True:
		print(f"ログイン(↑/↓:変更する項目を移動, タブ:変更する項目を一つ下に移動, スペース:選択された設定でログイン, {"d:選択された設定を削除, "if selection!=option_count-1 else ""}n:新規ログイン, q:終了):{"　　　　　　　　　　    "if selection==option_count-1 else ""}")
		for i,login_data in enumerate(config.login_datas):
			selected = selection==i
			print(f"{"\x1b[7m(*)\x1b[m"if selected else "( )"} {login_data.user_data.name}@{login_data.server_url}")
		i=option_count-1
		selected = selection==i
		print(f"{"\x1b[7m(*)\x1b[m"if selected else "( )"} （新規ログイン）")
		sys.stdout.flush()
		match getch():
			case b"\t":
				selection+=1
				selection%=option_count
			case b"q":
				raise SystemExit
			case b"n":
				tmp = try_new_login()
				if tmp is not None:
					return tmp
				print(f"\033[{option_count+1}E",end="")
			case b"d":
				if not selected:
					if ask_yes_no("本当に削除しますか","削除する","削除しない"):
						config.login_datas.pop(selection)
						option_count-=1
						save_config()
					print("\n"*(option_count+1),end="")
			case b"\r"|b" ":
				if selected:
					tmp = try_new_login()
				else:
					tmp = Session.login(config.login_datas[selection])
				if tmp is not None:
					return tmp
				elif not selected:
					status="\x1b[41m\x1b[37mログインに失敗しました。\x1b[0m"
				else:
					print(f"\033[{option_count+1}E",end="")
			case b"\xe0":
				match getch():
					case b"H":
						selection-=1
						selection%=option_count
					case b"P":
						selection+=1
						selection%=option_count
			case b"\x1b":
				# print(r"\x1e",file=sys.stderr)
				if getch()==b"[":
					# print(r"[",file=sys.stderr)
					match getch():
						case b"A":
							selection-=1
							selection%=option_count
						case b"B":
							selection+=1
							selection%=option_count
						# case c:
						# 	print(repr(c),file=sys.stderr)
		print(f"{status}\033[{option_count+1}F",end="")
def try_new_login()->Session|None:
	while not (server_url:=input("接続先のサーバーのURL(ローカルのものの場合は通常は「https://localhost:8080/」): ")):
		print("URLを入力して下さい。")
	while not (user_name:=input("ユーザー名(改行は使用不可です): ")):
		print("ユーザー名を入力して下さい。")
	while True:
		while not (password:=getpass("パスワード(打ち間違えた場合はエンターを押してください): ")):
			print("パスワードを入力して下さい。")
		if password_:=getpass("パスワード(確認)(先ほど打ち間違えた場合はなにも入れずにエンターを押してください): "):
			if password==password_:
				break
			print("一致しませんでした。再度入力してください。")
	login_data=LoginData(server_url,UserData(user_name,password))
	if (session:=Session.login(login_data))is None:
		print("ログインに失敗しました。")
		if not ask_yes_no("アカウントの作成を試みますか","作成を試みる","作成を試みない"):
			return None
		if (session:=Session.signup(login_data))is None:
			print("アカウントの作成に失敗しました。")
			return None
		print("アカウントの作成に成功しました。この情報を保存すると、以降は簡単にログインすることができます。")
	else:
		print("ログインに成功しました。この情報を保存すると、以降は簡単にログインすることができます。")
	if ask_yes_no("保存しますか","保存する","保存しない"):
		config.login_datas.append(login_data)
		save_config()
	return session
def setting():
	while True:
		match select("設定", [
			"デフォルト難易度設定",
			"戻る"
		],value_on_q=1):
			case 0:
				if (tmp:=configure(config.difficulty)) is not None:
					config.difficulty = tmp
					save_config()
			case 1:
				break