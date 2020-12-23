from base64 import  b64decode, b64encode
import json 
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes

class Cipher():
    """ Класс шифровальшик """
    @staticmethod
    def encrypt(text, key): 
        data = bytes(text, encoding='utf-8')
        while len(key) != 32: 
            key += ' '
        key = bytes(key, encoding='utf-8')
        cipher = AES.new(key, AES.MODE_SIV)
        json_k = ["text", "tag"]
        json_v = [b64encode(x).decode('utf-8') for x in cipher.encrypt_and_digest(data)]
        return json.dumps(dict(zip(json_k, json_v)))

    @staticmethod
    def decrypt(data, key): # Рассмотреть добавление nonce, раз все равно пришел к json
        # Доводим до ума ключ 
        while len(key) != 32: 
            key += ' '
        key = bytes(key, encoding='utf-8')
        # Разбираем Json 
        b64 = json.loads(data)
        jk = ["text", "tag"]
        jv = {k:b64decode(b64[k]) for k in jk}
        # Дешифруем сообщение 
        cipher = AES.new(key, AES.MODE_SIV)
        text = cipher.decrypt_and_verify(jv["text"], jv["tag"])
        # Возвращаем текст
        return text