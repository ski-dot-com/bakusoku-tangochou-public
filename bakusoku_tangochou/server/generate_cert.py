from os import remove
from os.path import exists, isdir
from shutil import rmtree

import cryptography.x509 as x509
import cryptography.x509.oid as oid
import cryptography.hazmat.primitives.serialization as serialization
import cryptography.hazmat.primitives.hashes as hashes
import cryptography.hazmat.primitives.asymmetric.rsa as rsa
import datetime

from ..core.util import ask_yes_no

def generate_cert(cert_path:str="cert.pem",key_path:str="key.pem",continue_if_exist:bool|None=None):
	if exists(cert_path) or exists(key_path):
		if continue_if_exist is None:
			print("指定されたバスには既にデータが存在します。")
			if not ask_yes_no("置換しますか","置換する", "置換せず、プログラムを終了する"):
				return
		elif not continue_if_exist:
			print("Error: 指定されたバスには既にデータが存在しました。")
			return
		if exists(cert_path):
			if isdir(cert_path):
				rmtree(cert_path)
			else:
				remove(cert_path)
		if exists(key_path):
			if isdir(key_path):
				rmtree(key_path)
			else:
				remove(key_path)
	priv=rsa.generate_private_key(65537,2048)
	with open(key_path,"wb") as f:
		f.write(priv.private_bytes(
			serialization.Encoding.PEM,
			serialization.PrivateFormat.PKCS8,
			serialization.NoEncryption()
		))
	name=x509.Name([
		x509.NameAttribute(oid.NameOID.COMMON_NAME, "localhost")
	])
	with open(cert_path,"wb") as f:
		now=datetime.datetime.now(datetime.timezone.utc)
		f.write(
			x509.CertificateBuilder()
				.public_key(priv.public_key())
				.subject_name(name)
				.issuer_name(name)
				.serial_number(x509.random_serial_number())
				.not_valid_before(now)
				.not_valid_after(now+datetime.timedelta(365))
				.sign(priv, hashes.SHA256())
				.public_bytes(serialization.Encoding.PEM)
		)