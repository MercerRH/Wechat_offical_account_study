"""模型类模块"""
from wechat import db
import datetime


class Questionnaire(db.Model):
    """问卷类"""
    __tablename__ = "Questionnaire"

    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    request = db.Column(db.Text, nullable=False)
    create_data = db.Column(db.DateTime, default=datetime.datetime.now)

    # create_usr = db.Column(db.String)

    def __str__(self):
        return self.title
