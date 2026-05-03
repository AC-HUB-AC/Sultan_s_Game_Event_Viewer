# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 19:49:39 2025

@author: 阿赤
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import glob
import re

class EventViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("事件分支查看器")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # 设置中文字体
        self.font = ('Microsoft YaHei UI', 10)
        
        # 数据
        self.event_files = []
        self.event_data = {}
        self.current_event = None
        self.current_settlement = None
        self.comments_data = {}  # 存储注释信息
        self.all_event_names = []  # 存储所有事件名称
        
        # 设置暗黑主题
        self.set_dark_theme()
        
        # 创建UI
        self.create_ui()
        
        # 加载数据
        self.load_event_files()
    
    def set_dark_theme(self):
        """设置暗黑主题颜色"""
        # 基础颜色
        bg_color = "#1e1e1e"        # 背景色
        fg_color = "#d4d4d4"         # 前景色（文字）
        select_bg = "#264f78"        # 选中背景
        select_fg = "#ffffff"        # 选中前景
        input_bg = "#3c3c3c"         # 输入框背景
        border_color = "#555555"     # 边框颜色
        
        # 配置ttk样式
        style = ttk.Style()
        
        # 尝试使用暗黑主题
        try:
            style.theme_use("clam")  # 使用可定制性高的主题作为基础
        except:
            pass
        
        # 配置各种元素的样式
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=self.font)
        style.configure("TButton", background=input_bg, foreground=fg_color, font=self.font)
        style.configure("TEntry", fieldbackground=input_bg, foreground=fg_color, font=self.font)
        style.configure("TCombobox", background=input_bg, fieldbackground=input_bg, foreground=fg_color, font=self.font)
        style.map("TCombobox", fieldbackground=[("readonly", input_bg)], foreground=[("readonly", fg_color)])
        
        # 树形视图样式
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color, 
                        font=self.font)
        style.configure("Treeview.Heading", 
                        background=input_bg, 
                        foreground=fg_color, 
                        font=self.font)
        style.map("Treeview", 
                 background=[("selected", select_bg)],
                 foreground=[("selected", select_fg)])
        
        # LabelFrame样式
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color, font=self.font)
        
        # 滚动条样式
        style.configure("TScrollbar", background=input_bg, troughcolor=bg_color, bordercolor=border_color)
        
        # 设置根窗口颜色
        self.root.configure(background=bg_color)
        
        # 返回颜色以供其他部分使用
        return {
            "bg": bg_color,
            "fg": fg_color,
            "select_bg": select_bg,
            "select_fg": select_fg,
            "input_bg": input_bg,
            "border": border_color
        }
        
    def create_ui(self):
        # 获取颜色方案
        colors = self.set_dark_theme()
        
        # 创建主框架 - 去掉边框
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        
        # 创建顶部控制区
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件夹选择
        ttk.Label(control_frame, text="文件夹:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        self.folder_path = tk.StringVar(value="如果官方有更新，选择你的游戏文件夹，Sultan's Game\Sultan's Game_Data\StreamingAssets\config\rite")
        folder_entry = ttk.Entry(control_frame, textvariable=self.folder_path)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(control_frame, text="浏览", command=self.browse_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="加载", command=self.load_event_files).pack(side=tk.LEFT)
        
        # 玩家名称设置
        player_frame = ttk.Frame(main_frame)
        player_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(player_frame, text="玩家名称 [player.name]:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        self.player_name = tk.StringVar(value="玩家")
        player_entry = ttk.Entry(player_frame, textvariable=self.player_name)
        player_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.player_name.trace_add("write", self.on_player_name_change)
        
        # 事件选择框架 - 单个组合框
        event_select_frame = ttk.Frame(main_frame)
        event_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 事件选择 - 搜索+下拉一体化
        ttk.Label(event_select_frame, text="事件:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        
        # 使用Combobox的搜索功能
        self.event_combo = ttk.Combobox(event_select_frame, font=self.font, width=80)
        self.event_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.event_combo.bind("<KeyRelease>", self.filter_events)
        self.event_combo.bind("<<ComboboxSelected>>", self.on_event_selected)
        
        # 创建事件描述区域 - 去掉边框
        description_frame = ttk.Frame(main_frame)
        description_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(description_frame, text="事件描述", font=self.font).pack(anchor=tk.W)
        
        # 事件描述文本
        self.event_desc_text = scrolledtext.ScrolledText(description_frame, wrap=tk.WORD, font=self.font, height=3)
        self.event_desc_text.pack(fill=tk.X, expand=True)
        # 设置文本颜色
        self.event_desc_text.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["fg"])
        
        # 创建中间区域 - 分为左右两列
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        middle_frame.grid_columnconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(1, weight=1)
        
        # 左侧 - Slot条件列表 - 去掉边框
        slot_frame = ttk.Frame(middle_frame)
        slot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ttk.Label(slot_frame, text="Slot条件列表", font=self.font).pack(anchor=tk.W)
        
        # Slot条件列表
        self.slot_tree = ttk.Treeview(slot_frame, columns=("id", "description"), show="headings", height=8)
        self.slot_tree.heading("id", text="ID")
        self.slot_tree.heading("description", text="条件描述")
        self.slot_tree.column("id", width=80)
        self.slot_tree.column("description", width=400)
        
        # 添加滚动条
        slot_scrollbar = ttk.Scrollbar(slot_frame, orient="vertical", command=self.slot_tree.yview)
        self.slot_tree.configure(yscrollcommand=slot_scrollbar.set)
        
        # 放置树形视图和滚动条
        self.slot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        slot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.slot_tree.bind("<<TreeviewSelect>>", self.on_slot_selected)
        
        # 右侧 - Settlement条件列表 - 去掉边框
        settlement_frame = ttk.Frame(middle_frame)
        settlement_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ttk.Label(settlement_frame, text="Settlement条件列表", font=self.font).pack(anchor=tk.W)
        
        # Settlement条件列表
        self.settlement_tree = ttk.Treeview(settlement_frame, columns=("id", "description"), show="headings", height=8)
        self.settlement_tree.heading("id", text="ID")
        self.settlement_tree.heading("description", text="条件描述")
        self.settlement_tree.column("id", width=80)
        self.settlement_tree.column("description", width=400)
        
        # 添加滚动条
        settlement_scrollbar = ttk.Scrollbar(settlement_frame, orient="vertical", command=self.settlement_tree.yview)
        self.settlement_tree.configure(yscrollcommand=settlement_scrollbar.set)
        
        # 放置树形视图和滚动条
        self.settlement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        settlement_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.settlement_tree.bind("<<TreeviewSelect>>", self.on_settlement_selected)
        
        # 创建结果文本区域 - 去掉边框
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
                
        # 结果标题
        self.result_title_var = tk.StringVar()
        title_label = ttk.Label(result_frame, textvariable=self.result_title_var, font=('Microsoft YaHei UI', 12, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 结果文本
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=self.font)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        # 设置文本颜色
        self.result_text.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["fg"])
        # 配置标签样式
        self.result_text.tag_configure("title", font=("Microsoft YaHei UI", 12, "bold"))
        self.result_text.tag_configure("content", font=("Microsoft YaHei UI", 10))
        self.result_text.tag_configure("comment", font=("Microsoft YaHei UI", 10, "italic"), foreground="#6a9955")
        
    def browse_folder(self):
        folder = tk.filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.load_event_files()
    
    def filter_events(self, event=None):
        """根据输入过滤事件列表"""
        if not hasattr(self, 'all_event_names') or not self.all_event_names:
            # 首次调用时确保有完整的事件列表
            return
        
        # 获取当前输入的文本
        search_text = self.event_combo.get().lower()
        
        # 避免在事件处理中弹出下拉菜单导致输入中断
        if event and event.keysym in ('Down', 'Up', 'Return', 'Tab'):
            return
        
        # 延迟执行筛选，避免在输入过程中频繁触发
        if hasattr(self, '_filter_job'):
            self.root.after_cancel(self._filter_job)
        
        self._filter_job = self.root.after(500, lambda: self._do_filter(search_text))
    
    def _do_filter(self, search_text):
        """实际执行筛选操作"""
        # 如果搜索框为空，显示所有事件
        if not search_text:
            self.event_combo["values"] = self.all_event_names
        else:
            # 筛选包含搜索文本的事件
            filtered_events = [name for name in self.all_event_names if search_text in name.lower()]
            self.event_combo["values"] = filtered_events
            
            # 保持下拉列表打开
            if filtered_events:
                self.event_combo.event_generate('<Down>')
    
    def extract_comments(self, content):
        """从JSON内容中提取注释"""
        comments = {}
        
        # 匹配 "key":value //comment 格式的注释
        comment_pattern = r'"([^"]+)":\s*([^,\{\}\[\]]+|\"[^\"]*\"|true|false|null),?\s*//(.+?)(?=\n|$)'
        matches = re.finditer(comment_pattern, content)
        
        for match in matches:
            key = match.group(1)
            value = match.group(2).strip()
            comment = match.group(3).strip()
            
            # 构建键，形如 "key:value"
            comment_key = f"{key}:{value}"
            comments[comment_key] = comment
        
        # 匹配行末尾带有注释的对象和数组值
        object_comment_pattern = r'"([^"]+)":\s*(\{|\[)\s*//(.+?)(?=\n|$)'
        matches = re.finditer(object_comment_pattern, content)
        
        for match in matches:
            key = match.group(1)
            comment = match.group(3).strip()
            comments[key] = comment
        
        # 匹配单独的键值对末尾的注释（不依赖于值的类型）
        key_value_pattern = r'"([^"]+)":\s*([^,\n]*),?\s*//(.+?)(?=\n|$)'
        matches = re.finditer(key_value_pattern, content)
        
        for match in matches:
            key = match.group(1)
            value = match.group(2).strip()
            comment = match.group(3).strip()
            
            if value and value not in ['{', '[']:
                comment_key = f"{key}:{value}"
                if comment_key not in comments:
                    comments[comment_key] = comment
            else:
                if key not in comments:
                    comments[key] = comment
        
        return comments
    
    def on_player_name_change(self, *args):
        """当玩家名称改变时，更新显示的文本"""
        if self.current_settlement:
            self.display_result_text(self.current_settlement)
    
    def format_condition(self, condition, comments=None):
        """格式化条件为可读文本，可选添加注释"""
        if not condition:
            return "无条件"
        
        # 简单展示条件内容
        condition_str = json.dumps(condition, ensure_ascii=False)
        
        # 添加注释（如果有）
        if comments:
            comment_parts = []
            for key, value in condition.items():
                comment_key = f"{key}:{value}"
                if comment_key in comments:
                    comment_parts.append(f"{comments[comment_key]}")
                elif key in comments:
                    comment_parts.append(f"{comments[key]}")
            
            if comment_parts:
                condition_str = " ".join(comment_parts) + condition_str
        
        return condition_str
    
    def load_event_files(self):
        # 获取程序所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置默认文件夹为当前目录下的rite文件夹
        default_folder = os.path.join(current_dir, "rite")
        
        # 只有在路径为空或仍是初始提示语时才使用默认路径
        folder = self.folder_path.get()
        if not folder or "如果官方有更新" in folder:
            self.folder_path.set(default_folder)
            folder = default_folder
        self.event_files = []
        self.event_data = {}
        self.comments_data = {}
        
        try:
            # 查找所有json文件
            json_files = glob.glob(os.path.join(folder, "*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 提取注释信息
                        self.comments_data[file_path] = self.extract_comments(content)
                        
                        # 尝试修复常见的JSON错误
                        # 1. 移除//类型的注释，但先保存它们以便后续显示
                        content_no_comments = re.sub(r'//.*', '', content)
                        
                        # 2. 末尾多余的逗号问题
                        content_no_comments = re.sub(r',\s*([}\]])', r'\1', content_no_comments)
                        
                        # 3. 清理剩余可能导致问题的格式
                        content_no_comments = re.sub(r'(?m)^\s*//.*$', '', content_no_comments)  # 删除整行注释
                        
                        try:
                            # 尝试使用标准JSON解析
                            data = json.loads(content_no_comments)
                            # 检查是否是事件数据
                            if 'id' in data and 'name' in data and 'settlement' in data:
                                self.event_files.append(file_path)
                                self.event_data[file_path] = data
                        except json.JSONDecodeError as je:
                            print(f"JSON解析错误: {file_path}, 错误: {je}")
                            
                except Exception as e:
                    print(f"加载文件出错: {file_path}, 错误: {e}")
            
            # 更新事件下拉列表
            event_names = []
            for file_path in self.event_files:
                event_data = self.event_data[file_path]
                event_names.append(f"{event_data['id']} - {event_data['name']}")
            
            # 按ID排序事件列表
            event_names.sort(key=lambda x: int(x.split(' - ')[0]) if x.split(' - ')[0].isdigit() else float('inf'))
            
            self.event_combo["values"] = event_names
            # 保存所有事件名称以便筛选
            self.all_event_names = event_names.copy()
            
            if event_names:
                self.event_combo.set("")  # 初始化为空，允许用户输入搜索
                messagebox.showinfo("提示", f"成功加载了 {len(self.event_files)} 个事件文件")
            else:
                messagebox.showinfo("提示", "没有找到有效的事件文件")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载事件文件时出错: {e}")
    
    def on_event_selected(self, event):
        """当从下拉列表选择事件时调用"""
        selected_event = self.event_combo.get()
        if not selected_event:
            return
            
        # 查找对应的事件文件
        for file_path in self.event_files:
            event_data = self.event_data[file_path]
            event_name = f"{event_data['id']} - {event_data['name']}"
            if event_name == selected_event:
                self.current_event = file_path
                
                # 更新事件描述文本
                self.event_desc_text.delete(1.0, tk.END)
                if 'text' in event_data:
                    self.event_desc_text.insert(tk.END, event_data['text'])
                
                # 更新条件列表
                self.update_condition_lists()
                break
    
    def update_condition_lists(self):
        """更新条件列表"""
        if not self.current_event:
            return
        
        # 清空树形视图
        for item in self.slot_tree.get_children():
            self.slot_tree.delete(item)
        
        for item in self.settlement_tree.get_children():
            self.settlement_tree.delete(item)
        
        event_data = self.event_data[self.current_event]
        comments = self.comments_data.get(self.current_event, {})
        
        # 添加slot条件
        if "cards_slot" in event_data:
            for slot_key, slot_info in event_data["cards_slot"].items():
                if "condition" in slot_info:
                    condition_desc = self.format_condition(slot_info["condition"], comments)
                    slot_text = slot_info.get("text", "")
                    # 显示最多200个字符，避免过长
                    full_text = f"{condition_desc} - {slot_text}"
                    display_text = full_text[:200] + "..." if len(full_text) > 200 else full_text
                    self.slot_tree.insert("", "end", values=(f"s{slot_key}", display_text))
        
        # 整理settlement条件 - 按条件归类
        condition_groups = {}
        
        # 处理settlement
        if "settlement" in event_data:
            for i, settlement in enumerate(event_data["settlement"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("settlement", i, settlement))
        
        # 处理settlement_prior
        if "settlement_prior" in event_data:
            for i, settlement in enumerate(event_data["settlement_prior"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("prior", i, settlement))
        
        # 处理settlement_extre
        if "settlement_extre" in event_data:
            for i, settlement in enumerate(event_data["settlement_extre"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("extre", i, settlement))
        
        # 添加分组后的条件到树中
        group_index = 0
        for condition_key, group in condition_groups.items():
            condition = json.loads(condition_key)
            condition_desc = self.format_condition(condition, comments)
            display_text = condition_desc[:200] + "..." if len(condition_desc) > 200 else condition_desc
            
            # 添加组条目
            group_id = f"group_{group_index}"
            self.settlement_tree.insert("", "end", group_id, values=(f"条件组 {group_index}", display_text))
            
            # 添加组内每个条目
            for item_type, item_index, item in group:
                title = item.get("result_title", "无标题")
                title_display = title[:80] + "..." if len(title) > 80 else title if title else "无标题"
                value_id = f"{item_type}_{item_index}"
                self.settlement_tree.insert(group_id, "end", values=(value_id, title_display))
            
            group_index += 1
                    
        # 修改添加random_text条件的部分
        if "random_text_up" in event_data:
            for key, random_text in event_data["random_text_up"].items():
                if isinstance(random_text, dict) and "text" in random_text:
                    display_text = f"随机文本 {key}: {random_text['text'][:100]}"
                    if len(random_text["text"]) > 100:
                        display_text += "..."
                    self.settlement_tree.insert("", "end", values=(f"random_{key}", display_text))
        
    def display_result_text(self, settlement):
        """显示结果文本，替换玩家名称并添加注释"""
        # 保存当前settlement以便名称变更时更新
        self.current_settlement = settlement
        
        # 显示结果标题
        title = settlement.get("result_title", "无标题")
        self.result_title_var.set(title)
        
        # 显示结果文本，替换玩家名称
        result_text = settlement.get("result_text", "无结果文本")
        player_name = self.player_name.get() if self.player_name.get() else "玩家"
        result_text = result_text.replace("[player.name]", player_name)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_text)  
        
        # 获取结果文本末尾注释
        comments = self.comments_data.get(self.current_event, {})
        result_text_comment = comments.get("result_text", "")
        if result_text_comment:
            self.result_text.insert(tk.END, f"\n// {result_text_comment}", "content")

        # 附加显示条件详情
        if "condition" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 条件详情 ---\n", "title")
            
            # 获取当前事件的注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 格式化条件并添加注释
            for key, value in settlement["condition"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
        
        # 附加显示结果效果
        if "result" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 结果效果 ---\n", "title")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示结果并添加注释
            for key, value in settlement["result"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
        
        # 附加显示后续行动
        if "action" in settlement:
            self.result_text.insert(tk.END, "\n\n--- 后续行动 ---\n", "title")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示行动并添加注释
            for key, value in settlement["action"].items():
                # 处理值，将其转换为字符串
                str_value = str(value)
                
                # 构建与注释匹配的键
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"{key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
    
    def on_slot_selected(self, event):
        """当选择Slot条件时显示相关信息"""
        selected_items = self.slot_tree.selection()
        if not selected_items or not self.current_event:
            return
        
        # 清除settlement树中的选择
        self.settlement_tree.selection_remove(self.settlement_tree.selection())
        
        selected_id = self.slot_tree.item(selected_items[0], "values")[0]
        event_data = self.event_data[self.current_event]
        
        # 获取真正的slot键（去掉's'前缀）
        slot_key = selected_id[1:] if selected_id.startswith("s") else selected_id
        
        if "cards_slot" in event_data and slot_key in event_data["cards_slot"]:
            slot_info = event_data["cards_slot"][slot_key]
            self.result_title_var.set(f"Slot {slot_key}信息")
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "插槽条件用于定义卡牌放置的规则。\n\n")
            
            # 获取注释
            comments = self.comments_data.get(self.current_event, {})
            
            # 显示条件和注释
            self.result_text.insert(tk.END, "--- 条件 ---\n", "title")
            
            if "condition" in slot_info:
                for k, v in slot_info["condition"].items():
                    comment_key = f"{k}:{v}"
                    comment = comments.get(comment_key, comments.get(k, ""))
                    
                    if comment:
                        self.result_text.insert(tk.END, f"{k}: {v}", "content")
                        self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                    else:
                        self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
            
            # 显示其他信息
            self.result_text.insert(tk.END, "\n--- 其他信息 ---\n", "title")
            for k, v in slot_info.items():
                if k != "condition":
                    if k == "pops" and isinstance(v, list):
                        self.result_text.insert(tk.END, f"{k}:\n", "content")
                        self.format_pops_list(v, comments)
                    else:
                        comment_key = f"{k}:{v}"
                        comment = comments.get(comment_key, comments.get(k, ""))
                        
                        if comment:
                            self.result_text.insert(tk.END, f"{k}: {v}", "content")
                            self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                        else:
                            self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
                            
    def format_pops_list(self, pops_list, comments):
        """格式化pops列表，使其更有结构且仅显示关键信息"""
        indent = "    "  # 基本缩进
        
        for i, pop in enumerate(pops_list):
            self.result_text.insert(tk.END, f"{indent}[\n", "content")
            
            # 处理condition部分
            if "condition" in pop:
                self.result_text.insert(tk.END, f"{indent*2}\"condition\": {{\n", "content")
                for k, v in pop["condition"].items():
                    # 保留有意义的条件:
                    # 1. 包含中文字符的键值
                    # 2. 所有类型指示符(type)
                    # 3. 所有ID相关的键值(is, s1.is)
                    # 4. 所有比较运算符(>=, <, >, <=)
                    # 5. 所有否定条件(!xxx)
                    # 6. 所有计数器相关条件(counter.)
                    # 7. 所有状态检查(have.)
                    is_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(k) + str(v))
                    is_key_condition = (k.startswith("!") or 
                                      k.startswith("s1.") or
                                      "counter." in k or
                                      "have." in k or
                                      k in ["type", "is"] or 
                                      k.endswith(">=") or k.endswith("<") or 
                                      k.endswith(">") or k.endswith("<="))
                    
                    if is_chinese or is_key_condition:
                        comment_key = f"{k}:{v}"
                        comment = comments.get(comment_key, comments.get(k, ""))
                        
                        value_str = json.dumps(v, ensure_ascii=False)
                        if comment:
                            self.result_text.insert(tk.END, f"{indent*3}\"{k}\": {value_str}", "content")
                            self.result_text.insert(tk.END, f" // {comment}\n", "comment")
                        else:
                            self.result_text.insert(tk.END, f"{indent*3}\"{k}\": {value_str}\n", "content")
                self.result_text.insert(tk.END, f"{indent*2}}},\n", "content")
            
            # 处理action部分，只保留有解释意义的内容
            if "action" in pop:
                # 检查是否有解释性文本
                has_meaningful_text = False
                text_content = ""
                
                if "choose" in pop["action"] and isinstance(pop["action"]["choose"], dict):
                    for key, value in pop["action"]["choose"].items():
                        if key.startswith("pop.") and isinstance(value, str) and value:
                            has_meaningful_text = True
                            text_content = value
                            break
                
                # 如果没有choose但有直接的pop.xxxx.self值
                elif any(k.startswith("pop.") for k in pop["action"].keys()):
                    for key, value in pop["action"].items():
                        if key.startswith("pop.") and isinstance(value, str) and value:
                            has_meaningful_text = True
                            text_content = value
                            break
                
                # 只展示有意义的解释文本，去掉花括号和引号
                if has_meaningful_text:
                    self.result_text.insert(tk.END, f"{indent*2}\"action\": \"{text_content}\"\n", "content")
            
            self.result_text.insert(tk.END, f"{indent}]\n", "content")
            
            # 添加一个分隔
            if i < len(pops_list) - 1:
                self.result_text.insert(tk.END, "\n", "content")

    def on_settlement_selected(self, event):
        """当选择Settlement条件时显示相关信息"""
        selected_items = self.settlement_tree.selection()
        if not selected_items or not self.current_event:
            return
        
        # 清除slot树中的选择
        self.slot_tree.selection_remove(self.slot_tree.selection())
        
        selected_id = self.settlement_tree.item(selected_items[0], "values")[0]
        event_data = self.event_data[self.current_event]
        
        # 检查是否是组标题
        if selected_id.startswith("条件组 "):
            # 如果选择了组标题，显示此组所有结果的合并
            group_index = int(selected_id.split(" ")[1])
            self.display_group_results(group_index)
            return
        
        if selected_id.startswith("prior_"):
            # 处理settlement_prior条件
            index = int(selected_id.split("_")[1])
            if "settlement_prior" in event_data and 0 <= index < len(event_data["settlement_prior"]):
                settlement = event_data["settlement_prior"][index]
                self.display_result_text(settlement)
        elif selected_id.startswith("extre_"):
            # 处理settlement_extre条件
            index = int(selected_id.split("_")[1])
            if "settlement_extre" in event_data and 0 <= index < len(event_data["settlement_extre"]):
                settlement = event_data["settlement_extre"][index]
                self.display_result_text(settlement)
        elif selected_id.startswith("random_"):
            # 处理random_text条件
            key = selected_id[len("random_"):]
            if "random_text_up" in event_data and key in event_data["random_text_up"]:
                random_text = event_data["random_text_up"][key]
                self.display_random_text(random_text, key)
        elif selected_id.startswith("settlement_"):
            # 处理普通settlement条件
            try:
                index = int(selected_id.split("_")[1])
                if "settlement" in event_data and 0 <= index < len(event_data["settlement"]):
                    settlement = event_data["settlement"][index]
                    self.display_result_text(settlement)
            except (ValueError, IndexError):
                pass
                
    def display_group_results(self, group_index):
        """显示同一条件组下的所有结果文本"""

    
        if not self.current_event:
            return
        
        event_data = self.event_data[self.current_event]
        
        # 重建条件组
        condition_groups = {}
        
        # 处理settlement
        if "settlement" in event_data:
            for i, settlement in enumerate(event_data["settlement"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("settlement", i, settlement))
        
        # 处理settlement_prior
        if "settlement_prior" in event_data:
            for i, settlement in enumerate(event_data["settlement_prior"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("prior", i, settlement))
        
        # 处理settlement_extre
        if "settlement_extre" in event_data:
            for i, settlement in enumerate(event_data["settlement_extre"]):
                if "condition" in settlement:
                    condition_key = json.dumps(settlement["condition"], sort_keys=True)
                    if condition_key not in condition_groups:
                        condition_groups[condition_key] = []
                    condition_groups[condition_key].append(("extre", i, settlement))
        
        # 获取指定组索引的组
        if len(condition_groups) <= group_index:
            return
        
        target_group = list(condition_groups.values())[group_index]
        

        self.result_title_var.set("结果文本")
        
        # 清空结果区
        self.result_text.delete(1.0, tk.END)
        
        
        
        # 显示所有结果
        for item_type, item_index, item in target_group:
            title = item.get("result_title", "")
            text = item.get("result_text", "")
            
            # 替换玩家名称
            player_name = self.player_name.get() if self.player_name.get() else "玩家"
            text = text.replace("[player.name]", player_name)
            
            # 不再显示标记，直接显示标题和文本
            if title:
                self.result_text.insert(tk.END, f"{title}\n", "title")
            
            self.result_text.insert(tk.END, f"{text}\n\n", "content")
            
            # 显示条件详情
            condition = json.loads(list(condition_groups.keys())[group_index])
            self.result_text.insert(tk.END, "--- 条件详情 ---\n", "title")
            comments = self.comments_data.get(self.current_event, {})
            
            for key, value in condition.items():
                str_value = str(value)
                comment_key = f"{key}:{str_value}"
                comment = comments.get(comment_key, comments.get(key, ""))
                
                if comment:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}", "content")
                    self.result_text.insert(tk.END, f"  // {comment}\n", "comment")
                else:
                    self.result_text.insert(tk.END, f"  {key}: {str_value}\n", "content")
            
            self.result_text.insert(tk.END, "\n", "content")
            
            # 显示结果效果和后续动作
            if "result" in item and item["result"]:
                self.result_text.insert(tk.END, "--- 结果效果 ---:\n", "title")
                for k, v in item["result"].items():
                    comment = self.comments_data.get(self.current_event, {}).get(f"{k}:{v}", "")
                    if comment:
                        self.result_text.insert(tk.END, f"  {k}: {v} // {comment}\n", "content")
                    else:
                        self.result_text.insert(tk.END, f"  {k}: {v}\n", "content")
                self.result_text.insert(tk.END, "\n")
            
            if "action" in item and item["action"]:
                self.result_text.insert(tk.END, "--- 后续动作 ---:\n", "title")
                for k, v in item["action"].items():
                    comment = self.comments_data.get(self.current_event, {}).get(f"{k}:{v}", "")
                    if comment:
                        self.result_text.insert(tk.END, f"  {k}: {v} // {comment}\n", "content")
                    else:
                        self.result_text.insert(tk.END, f"  {k}: {v}\n", "content")
                self.result_text.insert(tk.END, "\n")
            
            # 添加分隔线
            if target_group.index((item_type, item_index, item)) < len(target_group) - 1:
                self.result_text.insert(tk.END, "—" * 50 + "\n\n", "comment")
            
    def display_random_text(self, random_text, key):
        """显示随机文本信息"""
        self.result_title_var.set(f"随机文本 {key}")
        
        self.result_text.delete(1.0, tk.END)
        
        # 显示随机文本内容
        if isinstance(random_text, dict):
            # 随机文本是字典形式
            if "text" in random_text:
                text = random_text["text"]
                player_name = self.player_name.get() if self.player_name.get() else "玩家"
                text = text.replace("[player.name]", player_name)
                self.result_text.insert(tk.END, text + "\n\n", "content")
            
            # 显示其他属性
            for k, v in random_text.items():
                if k != "text":
                    self.result_text.insert(tk.END, f"{k}: {v}\n", "content")
                    # 检查是否有low_target等特殊属性
                    if k == "low_target" or k == "type" or k == "type_tips":
                        self.result_text.insert(tk.END, "\n", "content")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.title("苏丹的游戏 - 事件分支查看器")
            
        # 设置窗口尺寸和位置
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        app = EventViewer(root)
        root.mainloop()
    except Exception as e:
        import traceback
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"发生错误: {e}\n")
            f.write(traceback.format_exc())
        messagebox.showerror("错误", f"程序发生错误: {e}\n详细错误信息已保存到error_log.txt")