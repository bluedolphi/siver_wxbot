'''
邮件发送程序
作者：https://siver.top
时间：2025-03-05

email.txt文件格式：
第一行填发件人邮箱的SMTP服务器地址
第二行填发件人邮箱的SMTP服务器端口
第三行填写发件人邮箱
第四行填写邮箱授权码或密码

email.txt文件需要和email_send.py文件在同一目录下
'''

# 需要先安装安全传输层依赖库：pip install ssl
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ... existing code ...

email_path = '.\\email.txt'
def read_config(config_path=email_path):
    """从配置文件读取SMTP参数"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()[:4]]
            return {
                'host': lines[0],
                'port': int(lines[1]),  # 转换端口为整数
                'user': lines[2],
                'pass': lines[3]
            }
    except Exception as e:
        raise ValueError(f"配置文件读取失败: {str(e)}\n请检查email.txt文件是否正确")

# 读取配置文件
config = read_config()
mail_host = config['host']
mail_port = config['port']
mail_user = config['user']
mail_pass = config['pass']

# ... existing code remaining unchanged ...

def send_qq_email(receiver, subject, content):
    '''
    发送QQ邮箱邮件
    receiver: 收件人邮箱
    subject: 邮件主题
    content: 邮件内容
    '''
    # 创建MIMEText对象构建邮件内容
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header(mail_user)          # 发件人
    message['To'] = Header(receiver)             # 收件人
    message['Subject'] = Header(subject)         # 主题
    
    try:
        # 使用SSL加密连接SMTP服务器
        smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
        smtpObj.login(mail_user, mail_pass)      # 登录邮箱
        smtpObj.sendmail(mail_user, receiver, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException as e:
        print(f"邮件发送失败，错误：{str(e)}")
    finally:
        smtpObj.quit()
def send_email(receiver=mail_user, subject="默认邮件主题", content="这是来自Python程序的默认邮件内容"):
    '''
    发送邮件 默认给配置中的自己发邮件
    receiver: 收件人邮箱
    subject: 邮件主题
    content: 邮件内容
    '''
    send_qq_email(receiver, subject, content)

# 使用示例
if __name__ == "__main__":
    send_qq_email(
        receiver="666666@qq.com",  # 收件邮箱
        subject="测试邮件主题",
        content="这是来自Python程序的测试邮件内容"
    )