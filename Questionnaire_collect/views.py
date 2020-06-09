"""视图模块"""
from flask import request, abort, render_template
import hashlib
import xmltodict
import time
import json
from wechat import app
from models import Questionnaire
from wechat import db
import re
import requests

OPEN_ID = 'NULL'  # 获取的用户OPEN_ID


def SET_OPEN_ID(func):
    """获取用户OPEN_ID的装饰器
        注意！该装饰器只能由于让用户请求url的视图函数中
    """
    def func_in(*args, **kwargs):
        """获取用户OPEN ID"""
        code = request.args.get('code')  # 微信服务器返回的code，作为换取access_token的票据，5分钟过期
        state = request.args.get('state')  # 微信返回的state码

        # 请求网页授权access_token
        request_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx1e1d3b473be90fcf&secret" \
                      "=ef2d1efbd836fd49dcc4a2c4157ed931&code={}&grant_type=authorization_code".format(code)

        # 获取返回值，为一个json字符串
        response = requests.get(request_url)
        response_dict = response.json()
        # response_dict = json.loads(response_json)

        global OPEN_ID
        OPEN_ID = response_dict.get('openid')

        return func(*args, **kwargs)

    return func_in


# 进行微信公众号验证的视图
@app.route('/return_all', methods=['GET', 'POST'], endpoint='return_all')
def return_all():
    """用于获取用户发送的消息，及获取用户OPENID"""

    # 获取请求数据
    data = request.args
    data_dict = {}
    for i, s in data.items():
        data_dict[i] = s

    # 提取内容，这些字段不论是第一次验证还是以后发送数据都会存在
    signature = data_dict.get('signature')
    timestamp = data_dict.get('timestamp')
    nonce = data_dict.get('nonce')

    # 设置token
    token = 'test'

    # 对字符串进行拼接
    str_list = [token, timestamp, nonce]
    str_list.sort()
    s = "".join(str_list)
    signature_sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()

    # 判断是否由微信服务器发送的请求
    if signature != signature_sha1:
        abort(403)
    else:
        # 如果是，则判断是否为GET请求，是则表明是验证请求
        if request.method == 'GET':
            echostr = data_dict.get('echostr')
            if not echostr:
                abort(400)
            return echostr

        # 如果为POST请求则为微信转发来的消息
        elif request.method == 'POST':
            # 提取参数
            xml_str = request.data

            # 转为字典数据
            xml_dict = xmltodict.parse(xml_str)
            xml_content_dict = xml_dict.get('xml')

            # 提取数据
            FromUserName = xml_content_dict.get('FromUserName')
            ToUserName = xml_content_dict.get('ToUserName')
            Content = xml_content_dict.get('Content')
            MsgType = xml_content_dict.get('MsgType')

            # 构造回复数据
            xml_response_dict = {
                u'xml': {
                    u'ToUserName': FromUserName,
                    u'FromUserName': ToUserName,
                    u'CreateTime': int(time.time()),
                    u'MsgType': 'text',
                },
            }

            # 若传输的为文本数据
            if MsgType == 'text':
                # 根据命令返回数据
                xml_response_dict[u'xml']['Content'] = content_resp(Content, FromUserName)
                # 转为xml数据
                xml_response = xmltodict.unparse(xml_response_dict)

                return xml_response

            # 若传输的并非文本数据：
            else:
                xml_response_dict[u'xml'][u'Content'] = "无法识别，请输入文字数据"
                # 转为xml数据
                xml_response = xmltodict.unparse(xml_response_dict)

                return xml_response


def content_resp(Content, FromUserName):
    """用于对用户的命令作出响应"""

    # 公众号支持的文字命令列表
    COMMAND_LIST = ['帮助', '删除', '查询']

    # 获取用户请求的功能
    command = Content.split(' ')[0]

    # 判断命令是否在命令列表中
    if command in COMMAND_LIST:
        # 帮助
        if command == '帮助':
            resp_str = "您可以使用'删除+空格+问卷id'来删除问卷，例如：'删除 11111'。\n您也可以使用'查询'来查找您发布的问卷"
            return resp_str
        # 查询
        if command == '查询':
            resp_str_list = ['您的问卷：']
            q_all = Questionnaire.query.filter_by(openid=FromUserName).all()
            if q_all == []:
                return "您尚未发布问卷"
            else:
                for i in q_all:
                    id = i.id
                    title = i.title
                    resp_str_list.append('id：'+str(id)+'，标题：'+str(title))
                resp_str = "\n".join(resp_str_list)
                return resp_str
        # 删除
        if command == '删除':
            if len(Content.split(' ')) == 1:
                return "id输入不能为空"
            else:
                id = Content.split(' ')[1]
                if id == '':
                    return 'id输入不能为空'
                else:
                    q = Questionnaire.query.filter_by(openid=FromUserName, id=id).first()
                    if q == None:
                        return '未查询到id为{}的问卷'.format(id)
                    else:
                        db.session.delete(q)
                        db.session.commit()
                        return "删除成功"
    else:
        return "无法识别的命令，输入'帮助'查看命令列表"


# 提交问卷的视图
@app.route('/put/', endpoint='put')
@SET_OPEN_ID
def put():
    """显示添加问卷模板"""
    return render_template('put.html')


# 将问卷信息写入mysql数据库的视图
@app.route('/put_to_db/', methods=['GET', 'POST'], endpoint='put_to_db')
def put_to_db():
    # 获取POST数据
    title = request.form.get("q_title")
    url = request.form.get("q_url")
    request_str = request.form.get("q_request")

    global OPEN_ID
    q = Questionnaire(title=title, url=url, request=request_str, openid=OPEN_ID)

    # 返回json数据
    if re.match('^http[s]?://.*', url) == None:
        resp_json = {'res': 0, 'q_id': q.id}
    else:
        # 将数据存入数据库
        db.session.add(q)
        db.session.commit()

        resp_json = {'res': 1, 'q_id': q.id}
    return json.dumps(resp_json), 200


# 获取问卷列表信息的视图
@app.route('/get_list/', methods=['GET', 'POST'], endpoint='get_list')
def get_list():
    # 问卷总数
    q_all_count = Questionnaire.query.count()

    # 获取请求的页码，若无参数为0
    page = request.args.get('page', 1)

    # 判断是否需要分页，及分页的页数
    if q_all_count < 9:
        q_all = Questionnaire.query.all()
        data = {
            'q_all': q_all,
            'q_page_list': [0],
            'q_page': 0
        }

    else:
        q_page = q_all_count // 9 + 1
        q_all = Questionnaire.query.offset((int(page) - 1) * 9).limit(9).all()
        q_page_list = [str(i + 1) for i in range(q_page)]

        data = {
            'q_all': q_all,
            'q_page_list': q_page_list,
            'q_page': page
        }
        print(q_page_list)

    return render_template('get.html', data=data)
