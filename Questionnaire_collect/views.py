"""视图模块"""
from flask import request, abort, render_template
import hashlib
import xmltodict
import time
import json
from wechat import app
from models import Questionnaire
from wechat import db


# 进行微信公众号验证的视图
@app.route('/return_all', methods=['GET', 'POST'])
def return_all():
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
                xml_response_dict[u'xml'][u'Content'] = Content
                # 转为xml数据
                xml_response = xmltodict.unparse(xml_response_dict)

                return xml_response

            # 若传输的并非文本数据：
            else:
                xml_response_dict[u'xml'][u'Content'] = "无法识别，请输入文字数据"
                # 转为xml数据
                xml_response = xmltodict.unparse(xml_response_dict)

                return xml_response


# 提交问卷的视图
@app.route('/put/')
def put():
    return render_template('put.html')


# 将问卷信息写入mysql数据库的视图
@app.route('/put_to_db/', methods=['GET', 'POST'])
def put_to_db():
    # 获取POST数据
    title = request.form.get("q_title")
    url = request.form.get("q_url")
    request_str = request.form.get("q_request")

    # 将数据存入数据库
    q = Questionnaire(title=title, url=url, request=request_str)
    db.session.add(q)
    db.session.commit()

    # 返回插入成功
    resp_json = {'res': 1, 'q_id': q.id}
    return json.dumps(resp_json), 200


# 获取问卷列表信息的视图
@app.route('/get_list/', methods=['GET', 'POST'])
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
        q_page = q_all_count//9 + 1
        q_all = Questionnaire.query.offset((int(page)-1)*9).limit(9).all()
        q_page_list = [str(i+1) for i in range(q_page)]

        data = {
            'q_all': q_all,
            'q_page_list': q_page_list,
            'q_page': page
        }
        print(q_page_list)

    return render_template('get.html', data=data)
