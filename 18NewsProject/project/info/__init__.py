import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config

# 制定session保存的位置，一般保存在redis数据库的nosql数据库
# 注意使用的是扩展中的session，并不是flask中的session，需要添加扩展
from flask_session import Session


# 初始化数据库, 需要被manage.py外界访问，需要提取到外面
# 在flask中的很多扩展中都可以先初始化对象，然后再去调用init.app方法去关联app
db = SQLAlchemy()

# redis_store: StrictRedis = None
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    # 设置日志的记录等级,调试debug级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    # 自建log文件夹，不能把log日志传到github，但是需要上传这个空文件夹，否则报错，所以自建一个.keepgit文件在里面
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):

    # 配置日志，根据不同的模式配置不同的log等级
    setup_log(config_name)

    # 初始化FLASK对象
    # 因为静态文件static目录和当前app的__name__同级，所以不需要额外设置，templates也是
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化数据库, 需要被manage.py外界访问，需要提取到外面
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 初始化redis，这个StrictRedis是用来保存项目中的K-V，并不是保存session的redis
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)
    # 开启csrf保护， 源代码中显示，如果不符合csrf直接return请求
    CSRFProtect(app)
    # 设置session保存制定位置
    Session(app)

    # 注册蓝图, 如果下面的import放在上面的话，那么卡启动的时候就会报错
    # 因为一个包去导入另一个包然会最后一个views.py去导入redis_store的时候就发现当前的文件还有有执行到redis_store = None
    # 这个循环导入，就会还没定义这个redis_store，因此以后何时注册蓝图，何时导入这个蓝图，蓝图的导入不要放在顶部
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)

    return app