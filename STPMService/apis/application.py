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
