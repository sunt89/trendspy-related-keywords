import os
import itchat
import logging
from tabulate import tabulate

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def login_wechat():
    """登录微信"""
    try:
        itchat.auto_login(hotReload=True, enableCmdQR=2)
        logging.info("WeChat logged in successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to login WeChat: {str(e)}")
        return False

def is_logged_in():
    """检查是否已登录"""
    try:
        # 尝试获取登录状态
        return itchat.search_friends()
    except:
        return False

def search_contacts(query=None):
    """搜索微信联系人
    
    Args:
        query: 搜索关键词，支持备注名、微信号、昵称等，为空则显示所有联系人
    """
    if not is_logged_in():
        if not login_wechat():
            return
    
    # 获取所有好友
    friends = itchat.get_friends(update=True)
    
    # 准备显示的数据
    contact_data = []
    for friend in friends:
        if query is None or query.lower() in str(friend).lower():
            contact_data.append([
                friend['UserName'],  # 用户ID
                friend['RemarkName'] or '无备注',  # 备注名
                friend['NickName'],  # 昵称
                friend['Signature'][:20] + '...' if friend['Signature'] and len(friend['Signature']) > 20 else friend['Signature'] or '无签名'  # 签名
            ])
    
    # 使用 tabulate 格式化输出
    if contact_data:
        headers = ['UserName', '备注名', '昵称', '签名']
        print("\n" + tabulate(contact_data, headers=headers, tablefmt='grid'))
        print(f"\n共找到 {len(contact_data)} 个联系人")
    else:
        print("未找到匹配的联系人")

def search_groups(query=None):
    """搜索微信群
    
    Args:
        query: 搜索关键词，支持群名称，为空则显示所有群
    """
    if not is_logged_in():
        if not login_wechat():
            return
    
    # 获取所有群
    groups = itchat.get_chatrooms(update=True)
    
    # 准备显示的数据
    group_data = []
    for group in groups:
        if query is None or query.lower() in str(group).lower():
            group_data.append([
                group['UserName'],  # 群ID
                group['NickName'],  # 群名称
                len(group['MemberList']) if 'MemberList' in group else '未知',  # 成员数量
            ])
    
    # 使用 tabulate 格式化输出
    if group_data:
        headers = ['UserName', '群名称', '成员数量']
        print("\n" + tabulate(group_data, headers=headers, tablefmt='grid'))
        print(f"\n共找到 {len(group_data)} 个群")
    else:
        print("未找到匹配的群")

def main():
    """主函数"""
    setup_logging()
    
    while True:
        print("\n=== 微信联系人查询工具 ===")
        print("1. 搜索联系人")
        print("2. 搜索群")
        print("3. 显示所有联系人")
        print("4. 显示所有群")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-4): ").strip()
        
        if choice == '0':
            break
        elif choice in ['1', '2']:
            query = input("请输入搜索关键词: ").strip()
            if choice == '1':
                search_contacts(query)
            else:
                search_groups(query)
        elif choice == '3':
            search_contacts()
        elif choice == '4':
            search_groups()
        else:
            print("无效的选择，请重试")
    
    print("感谢使用！")

if __name__ == "__main__":
    main() 