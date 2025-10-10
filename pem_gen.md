# 秘钥生成

```
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

```
Country Name (2 letter code) [AU]:CN
State or Province Name (full name) [Some-State]:SZ
Locality Name (eg, city) []:SZ
Organization Name (eg, company) [Internet Widgits Pty Ltd]:ugreen
Organizational Unit Name (eg, section) []:
Common Name (e.g. server FQDN or YOUR name) []:
Email Address []:
```

python gradio_app.py

注意：需要停用代理
