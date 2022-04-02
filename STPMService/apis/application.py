from flask import Blueprint
from dbutils.pooled_db import PooledDB
from configs import config, format
import pymysql.cursors
from flask import request
import json

# 使用数据库连接池的方式链接数据库，提高资源利用率
pool = PooledDB(pymysql, mincached=2, maxcached=5, host=config.MYSQL_HOST, port=config.MYSQL_PORT,
                user=config.MYSQL_USER, passwd=config.MYSQL_PASSWORD, database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor)

app_application = Blueprint("app_application", __name__)


# def connectDB():
#     connection = pymysql.connect(host='localhost',   # 数据库IP地址或链接域名
#                                  user='root',        # 设置的具有增改查权限的用户
#                                  password='root',    # 用户对应的密码
#                                  database='STPMDatas',  # 数据表
#                                  charset='utf8mb4',  # 字符编码
#                                  cursorclass=pymysql.cursors.DictCursor)  # 结果作为字典返回游标
#     # 返回新的数据库链接对象
#     return connection


@app_application.route("/api/application/product", methods=['GET'])
def getProduct():
    # 初始化数据库链接
    connection = pool.connection()

    with connection.cursor() as cursor:
        # 查询产品信息表-按更新时间新旧排序
        sql = "SELECT id,keyCode,title FROM `products` WHERE `status`=0 ORDER BY `update` DESC"
        cursor.execute(sql)
        data = cursor.fetchall()

    # 按返回模版格式进行json结果返回
    response = format.resp_format_success
    response['data'] = data
    return response


@app_application.route("/api/application/search", methods=['POST'])
def searchBykey():
    body = request.get_data()
    body = json.loads(body)

    # 基础语句定义
    sql = ""

    # 获取pageSize和
    pageSize = 10 if body['pageSize'] is None else body['pageSize']
    currentPage = 1 if body['currentPage'] is None else body['currentPage']

    # 拼接查询条件
    if 'productId' in body and body['productId'] != '':
        sql = sql + " AND `productId` = '{}'".format(body['productId'])
    if 'appId' in body and body['appId'] != '':
        sql = sql + " AND `appId` LIKE '%{}%'".format(body['appId'])
    if 'note' in body and body['note'] != '':
        sql = sql + " AND `note` LIKE '%{}%'".format(body['note'])
    if 'tester' in body and body['tester'] != '':
        sql = sql + " AND `tester` LIKE '%{}%'".format(body['tester'])
    if 'developer' in body and body['developer'] != '':
        sql = sql + " AND `developer` LIKE '%{}%'".format(body['developer'])
    if 'producer' in body and body['producer'] != '':
        sql = sql + " AND `producer` LIKE '%{}%'".format(body['producer'])

    # 排序和页数拼接
    # sql = sql + ' ORDER BY `updateDate` DESC LIMIT {},{}'.format((currentPage - 1) * pageSize, pageSize)
    # print("我是上面的输出" + sql)

    # 初始化数据库链接
    connection = pool.connection()

    with connection:
        # 先查询总数
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as `count` FROM `apps` WHERE `status`=0' + sql)
            total = cursor.fetchall()
            print("1: ")
            print(total)

        sql = sql + ' ORDER BY `updateDate` DESC LIMIT {},{}'.format((currentPage - 1) * pageSize, pageSize)
        # 执行查询
        with connection.cursor() as cursor:
            # 按照条件进行查询
            cursor.execute('SELECT P.title, A.* FROM apps AS A,products AS P WHERE A.productId = P.id and A.`status`=0' + sql)
            sqll = 'SELECT P.title, A.* FROM apps AS A,products AS P WHERE A.productId = P.id and A.`status`=0' + sql
            # print("我是下面的输出 " + sqll)
            data = cursor.fetchall()

    # 按分页模版返回查询数据
    response = format.resp_format_success
    response['data'] = data
    # response['total'] = 15
    print("2: ")
    print(total)
    response['total'] = total[0]['count']
    print(response)
    return response


@app_application.route("/api/application/update", methods=['POST'])
def product_update():
    # 获取传递的数据，并转换成JSON
    body = request.get_data()
    body = json.loads(body)

    # 定义默认返回体
    resp_success = format.resp_format_success
    resp_failed = format.resp_format_failed

    # 判断必填参数
    if 'appId' not in body:
        resp_failed.message = '应用不能为空'
        return resp_failed
    elif 'tester' not in body:
        resp_failed.message = '测试负责人不能为空'
        return resp_failed
    elif 'developer' not in body:
        resp_failed.message = '开发负责人不能为空'
        return resp_failed
    elif 'producer' not in body:
        resp_failed.message = '产品负责人不能为空'
        return

    # 使用连接池链接数据库
    connection = pool.connection()

    # 判断增加或是修改逻辑
    with connection:
        # 如果传的值有ID，那么进行修改操作，否则为新增数据
        if 'id' in body and body['id'] != '':
            with connection.cursor() as cursor:
                # 拼接修改语句，由于应用名不可修改，不需要做重复校验appId
                sql = "UPDATE `apps` SET `productId`=%s, `note`=%s,`tester`=%s,`developer`=%s,`producer`=%s,`CcEmail`=%s, " \
                      "`gitCode`=%s, `wiki`=%s, `more`=%s, `creteUser`=%s, `updateUser`=%s, `updateDate`= NOW() WHERE id=%s"
                cursor.execute(sql, (body["productId"], body["note"], body["tester"], body["developer"], body['producer'], body["CcEmail"],
                                     body["gitCode"], body["wiki"], body["more"], body["creteUser"], body["updateUser"], body["id"]))
                # 提交执行保存更新数据
                connection.commit()
        else:
            # 新增需要判断appId是否重复
            with connection.cursor() as cursor:
                select = "SELECT * FROM `apps` WHERE `appId`=%s AND `status`=0"
                cursor.execute(select, (body["appId"],))
                result = cursor.fetchall()

            # 有数据说明存在相同值，封装提示直接返回
            if len(result) > 0:
                resp_failed["code"] = 20001
                resp_failed["message"] = "应用ID（唯一编码keyCode）已存在，请修改！"
                return resp_failed

            with connection.cursor() as cursor:
                # 拼接插入语句,并用参数化%s构造防止基本的SQL注入
                # 其中id为自增，插入数据默认数据设置的当前时间
                sql = "INSERT INTO `apps` (`appId`,`productId`,`note`,`tester`,`developer`,`producer`,`CcEmail`,`gitCode`" \
                      ",`wiki`,`more`,`creteUser`,`updateUser`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, (body["appId"], body["productId"], body["note"], body["tester"], body["developer"], body['producer'], body["CcEmail"],
                                     body["gitCode"], body["wiki"], body["more"], body["creteUser"], body["updateUser"]))
                # 提交执行保存新增数据
                connection.commit()

        return resp_success
