import os
import smtplib
import logging
import itchat
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import EMAIL_CONFIG, NOTIFICATION_CONFIG
import pandas as pd

class NotificationManager:
    def __init__(self):
        self.wechat_logged_in = False
        if NOTIFICATION_CONFIG['method'] in ['wechat', 'both']:
            self._init_wechat()

    def _init_wechat(self):
        """初始化微信登录"""
        try:
            # 使用hotReload=True来保持登录状态
            itchat.auto_login(hotReload=True, enableCmdQR=2)
            self.wechat_logged_in = True
            logging.info("WeChat logged in successfully")
        except Exception as e:
            logging.error(f"Failed to login WeChat: {str(e)}")
            self.wechat_logged_in = False

    def send_notification(self, subject, body, attachments=None):
        """发送通知，根据配置选择发送方式"""
        method = NOTIFICATION_CONFIG['method']
        success = True

        if method in ['email', 'both']:
            email_success = self._send_email(subject, body, attachments)
            success = success and email_success

        if method in ['wechat', 'both']:
            wechat_success = self._send_wechat(subject, body, attachments)
            success = success and wechat_success

        return success

    def _send_email(self, subject, body, attachments=None):
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['sender_email']
            msg['To'] = EMAIL_CONFIG['recipient_email']
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            if attachments:
                for filepath in attachments:
                    with open(filepath, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                    msg.attach(part)

            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                logging.info("Attempting to login to Gmail...")
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                logging.info("Login successful, sending email...")
                server.send_message(msg)
                
            logging.info(f"Email sent successfully: {subject}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            logging.error(f"Email configuration used: server={EMAIL_CONFIG['smtp_server']}, port={EMAIL_CONFIG['smtp_port']}")
            return False

    def _format_wechat_message(self, subject, body, report_data=None):
        """格式化微信消息内容"""
        # 移除HTML标签
        text = self._html_to_text(body)
        
        # 提取和格式化关键信息
        lines = text.split('\n')
        formatted_lines = []
        
        # 添加标题
        formatted_lines.append(f"📊 {subject}")
        formatted_lines.append("=" * 30)
        
        # 处理正文
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测是否是新的部分
            if line.endswith(':'):
                current_section = line
                formatted_lines.append(f"\n📌 {line}")
            elif line.startswith('Time Range:'):
                formatted_lines.append(f"🕒 {line}")
            elif line.startswith('Region:'):
                formatted_lines.append(f"🌍 {line}")
            elif line.startswith('Total keywords'):
                formatted_lines.append(f"📝 {line}")
            elif line.startswith('Successful'):
                formatted_lines.append(f"✅ {line}")
            elif line.startswith('Failed'):
                formatted_lines.append(f"❌ {line}")
            elif ':' in line and 'Growth:' in line:
                # 处理趋势数据行
                keyword, rest = line.split(':', 1)
                value = rest.split('Growth:', 1)[1].strip('() ')
                formatted_lines.append(f"↗️ {keyword.strip()}")
                formatted_lines.append(f"   增长幅度: {value}")
            else:
                formatted_lines.append(line)
        
        # 如果有报告数据，添加详细内容
        if report_data is not None and isinstance(report_data, pd.DataFrame):
            formatted_lines.append("\n📌 详细报告:")
            
            # 按关键词分组
            for keyword in report_data['keyword'].unique():
                keyword_data = report_data[report_data['keyword'] == keyword]
                formatted_lines.append(f"\n🔍 {keyword}")
                
                # 分别处理 rising 和 top 数据
                for trend_type in ['rising', 'top']:
                    type_data = keyword_data[keyword_data['type'] == trend_type]
                    if not type_data.empty:
                        formatted_lines.append(f"  {'↗️ 上升趋势' if trend_type == 'rising' else '⭐ 热门趋势'}:")
                        for _, row in type_data.iterrows():
                            formatted_lines.append(f"    • {row['related_keywords']} ({row['value']})")
        
        return '\n'.join(formatted_lines)

    def _send_wechat(self, subject, body, attachments=None):
        """发送微信通知"""
        try:
            if not self.wechat_logged_in:
                self._init_wechat()
                if not self.wechat_logged_in:
                    return False

            receiver = NOTIFICATION_CONFIG['wechat_receiver']
            
            # 如果是报告文件，读取内容并作为消息发送
            report_data = None
            if attachments and any(f.endswith('.csv') for f in attachments):
                csv_file = next(f for f in attachments if f.endswith('.csv'))
                try:
                    report_data = pd.read_csv(csv_file)
                except Exception as e:
                    logging.warning(f"Failed to read report CSV file: {str(e)}")
            
            # 格式化消息内容
            message = self._format_wechat_message(subject, body, report_data)
            
            # 发送文本消息
            itchat.send(message, toUserName=receiver)
            
            # 如果有非CSV附件，仍然发送它们
            if attachments:
                for filepath in attachments:
                    if not filepath.endswith('.csv'):
                        file_message = f"\n📎 正在发送文件: {os.path.basename(filepath)}"
                        itchat.send(file_message, toUserName=receiver)
                        itchat.send_file(filepath, toUserName=receiver)
            
            logging.info(f"WeChat message sent successfully: {subject}")
            return True
        except Exception as e:
            logging.error(f"Failed to send WeChat message: {str(e)}")
            return False

    def _html_to_text(self, html):
        """简单的HTML到纯文本转换"""
        # 移除HTML标签的简单实现
        # 在实际应用中可能需要使用更复杂的HTML解析器
        import re
        text = re.sub('<[^<]+?>', '', html)
        return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')

    def __del__(self):
        """清理微信登录状态"""
        if self.wechat_logged_in:
            try:
                itchat.logout()
            except:
                pass 