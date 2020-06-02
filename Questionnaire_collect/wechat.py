from flask import Flask, request, abort, render_template
import hashlib
import xmltodict
import time
import json

app = Flask(__name__)


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
@app.route('/test/')
def test():
    return render_template('put.html')


# 将问卷信息写入mysql数据库的视图
@app.route('/put_to_db/', methods=['GET', 'POST'])
def put_to_db():
    json_data = request.get_json()
    resp_json = {'res': 1}
    return json.dumps(resp_json), 200


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=80)
    app.run()
