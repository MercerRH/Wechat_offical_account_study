"""应用初始化模块"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建falsk实例对象
app = Flask(__name__)
# 连接数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:LP079qR8@127.0.0.1:3306/wechat'
db = SQLAlchemy(app)
