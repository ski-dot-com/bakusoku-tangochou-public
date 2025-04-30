import argparse

from .load import load_csv
from .generate_cert import generate_cert
from .server import serve

parser = argparse.ArgumentParser(description="爆速単語帳のサーバーです。")
subparsers=parser.add_subparsers(help="行いたい操作を指定します。")
load_parser = subparsers.add_parser("load", help="csvファイルを読み込み、コンテストをホストするためのデータベースファイルを作成します。")
load_parser.add_argument("csv_path",help="読み込むcsvファイルのパス。")
load_parser.add_argument("database_path",help="作成するデータベースファイルのパス。省略した場合は「default.db」。",default="default.db",nargs='?')
load_yes_no_group=load_parser.add_mutually_exclusive_group()
load_yes_no_group.add_argument("-y","--yes", action="store_true",help="与えられた新しいデータベースファイルのパスにデータが存在した場合に断りなくそれを削除して新規作成します。")
load_yes_no_group.add_argument("-n","--no", action="store_true",help="与えられた新しいデータベースファイルのパスにデータが存在した場合に断りなくエラーとします。")
load_parser.set_defaults(handler=lambda:load_csv(args.csv_path,args.database_path,True if args.yes else False if args.no else None))
generate_cert_parser = subparsers.add_parser("generate_cert", help="コンテストをホストするための自己署名証明書と秘密鍵を作成します。")
generate_cert_parser.add_argument("cert_path",help="作成する証明書ファイルのパス。省略した場合は「cert.pem」。",default="cert.pem",nargs='?')
generate_cert_parser.add_argument("key_path",help="作成する秘密鍵ファイルのパス。省略した場合は「key.pem」。",default="key.pem",nargs='?')
generate_cert_yes_no_group=generate_cert_parser.add_mutually_exclusive_group()
generate_cert_yes_no_group.add_argument("-y","--yes", action="store_true",help="与えられたパスにすでにファイルが存在した場合に断りなくそれを削除して新規作成します。")
generate_cert_yes_no_group.add_argument("-n","--no", action="store_true",help="与えられたパスにすでにファイルが存在した場合に断りなくエラーとします。")
generate_cert_parser.set_defaults(handler=lambda:generate_cert(args.cert_path,args.key_path,True if args.yes else False if args.no else None))
serve_parser = subparsers.add_parser("serve", help="データベースファイルや証明書ファイル、秘密鍵ファイルなどを用いてサーバーを起動します。")
serve_parser.add_argument("-d","--database",help="使用するデータベースファイルのパス。省略した場合は「default.db」。",default="default.db",nargs='?')
serve_parser.add_argument("-c","--cert",help="使用する証明書ファイルのパス。省略した場合は「cert.pem」。",default="cert.pem")
serve_parser.add_argument("-k","--key",help="使用する秘密鍵ファイルのパス。省略した場合は「key.pem」。",default="key.pem")
serve_parser.add_argument("-p","--port",help="使用するポートのポート番号。省略した場合は8080。",default=8080, type=int)
serve_parser.set_defaults(handler=lambda:serve(args.database,args.cert,args.key,args.port))
args=parser.parse_args()
if hasattr(args, "handler"):
	args.handler()
else:
	parser.print_help()