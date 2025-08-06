import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from PIL import Image
import tempfile
from pathlib import Path
import ctypes
import sys
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def is_user_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class IconReplacer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面应用图标批量替换工具")
        self.root.geometry("700x600")

        self.root.attributes('-topmost', True)  # 先置顶
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))  # 1秒后取消置顶

        # 图标文件夹路径
        self.icon_folder = ""
        # 支持的图标格式
        self.supported_formats = ['.ico', '.png', '.jpg', '.jpeg', '.bmp']
        # 备份文件夹
        self.backup_folder = None

        self.setup_gui()

    def add_application_manually(self):
        """弹窗让用户手动选择一个 .lnk 或 .exe，然后插入列表"""
        filetypes = [("快捷方式", "*.lnk"), ("可执行文件", "*.exe")]
        path = filedialog.askopenfilename(title="选择要替换图标的应用",
                                          filetypes=filetypes)
        if not path:
            return

        path = Path(path)
        app_name = path.stem
        # 避免重复
        for item_id in self.tree.get_children():
            if Path(self.tree.item(item_id, 'values')[2]) == path:
                messagebox.showinfo("提示", f"{app_name} 已在列表中")
                return

        # 取目标
        target = ""
        if path.suffix.lower() == ".lnk":
            info = self.get_shortcut_info(path)
            if info:
                target = info['target']
        else:
            target = str(path)

        # 匹配图标
        matching_icon = self.find_matching_icon(app_name)
        icon_display = Path(matching_icon).name if matching_icon else "无匹配"
        status = "有匹配图标" if matching_icon else "无匹配"

        self.tree.insert('', 'end', values=(
            "", app_name, str(path), target, icon_display, status))
        self.progress_var.set(f"已手动添加 {app_name}")

    def setup_gui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))


        # 选择图标文件夹
        ttk.Label(main_frame, text="选择图标文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)

        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(folder_frame, text="浏览", command=self.select_folder).grid(row=0, column=1, padx=(5, 0))

        # 操作选项
        options_frame = ttk.LabelFrame(main_frame, text="替换选项", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 选择图标文件夹
        ttk.Label(main_frame, text="选择图标文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)

        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(folder_frame, text="浏览", command=self.select_folder).grid(row=0, column=1, padx=(5, 0))

        # 操作选项
        options_frame = ttk.LabelFrame(main_frame, text="替换选项", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.method_var = tk.StringVar(value="shortcut")
        ttk.Radiobutton(options_frame, text="替换快捷方式图标（推荐，安全）",
                        variable=self.method_var, value="shortcut").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="替换可执行文件图标（需管理员权限）",
                        variable=self.method_var, value="executable").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        self.include_public_desktop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="包含公共桌面快捷方式 (推荐)",
                        variable=self.include_public_desktop_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        self.backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="替换时备份原快捷方式",
                        variable=self.backup_var).grid(row=1, column=1,sticky=tk.W, padx=5,pady=5)

        # 扫描结果显示
        ttk.Label(main_frame, text="发现的应用程序:").grid(row=3, column=0, sticky=tk.W, pady=(20, 5))

        # 创建表格
        columns = ('选择', '应用名称', '快捷方式路径', '目标程序', '匹配图标', '状态')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=12)

        # 定义列
        for col in columns:
            self.tree.heading(col, text=col)

        # 设置列宽
        self.tree.column('选择', width=50)
        self.tree.column('应用名称', width=120)
        self.tree.column('快捷方式路径', width=150)
        self.tree.column('目标程序', width=150)
        self.tree.column('匹配图标', width=120)
        self.tree.column('状态', width=100)

        self.tree.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=4, column=2, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 绑定双击事件来切换选择状态
        self.tree.bind('<Double-1>', self.toggle_selection)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="扫描应用", command=self.scan_applications).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="添加应用…", command=self.add_application_manually).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="全选", command=self.select_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="全不选", command=self.deselect_all).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="替换选中图标", command=self.replace_selected_icons).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="恢复备份", command=self.restore_backup).grid(row=0, column=5, padx=5)

        # 进度条和状态
        self.progress_var = tk.StringVar()
        self.progress_var.set("就绪 - 请选择图标文件夹并扫描应用程序")
        status_label = ttk.Label(main_frame, textvariable=self.progress_var, foreground="blue")
        status_label.grid(row=6, column=0, columnspan=2, pady=10)


        # 使用说明
        help_text = """使用说明：
1. 选择包含图标文件的文件夹（图标文件名应与应用名称匹配）
2. 点击"扫描应用"查看可替换的应用程序
3. 双击表格行来选择/取消选择要替换的应用
4. 点击"替换选中图标"开始替换"""

        # 正文
        help_label = ttk.Label(main_frame, text=help_text, foreground="gray", font=("SimSun", 8))
        help_label.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="w")

        # 署名，右对齐
        author_label = ttk.Label(main_frame, text="by Wu_Petrichor", foreground="gray", font=("SimSun", 8))
        author_label.grid(row=8, column=0, columnspan=2, sticky="e")  # e = 右侧

        help_label = ttk.Label(main_frame, text=help_text, foreground="gray", font=("SimHel", 8))
        help_label.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        folder_frame.columnconfigure(0, weight=1)

    def select_folder(self):
        """选择图标文件夹"""
        folder = filedialog.askdirectory(title="选择包含图标文件的文件夹")
        if folder:
            self.folder_var.set(folder)
            self.icon_folder = folder
            self.progress_var.set(f"已选择图标文件夹: {folder}")

    def toggle_selection(self, event):
        """切换选择状态"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = list(self.tree.item(item_id)['values'])
            values[0] = "√" if values[0] != "√" else ""
            self.tree.item(item_id, values=values)

    def select_all(self):
        """全选"""
        for item_id in self.tree.get_children():
            values = list(self.tree.item(item_id)['values'])
            if values[4] != "无匹配":  # 只选择有匹配图标的项目
                values[0] = "√"
                self.tree.item(item_id, values=values)

    def deselect_all(self):
        """全不选"""
        for item_id in self.tree.get_children():
            values = list(self.tree.item(item_id)['values'])
            values[0] = ""
            self.tree.item(item_id, values=values)

    def get_shortcuts(self):
        """获取当前用户桌面和可选的公共桌面快捷方式"""
        shortcuts = []
        desktop_paths = [Path.home() / "Desktop"]

        if self.include_public_desktop_var.get():
            public_desktop = Path("C:/Users/Public/Desktop")
            if public_desktop.exists():
                desktop_paths.append(public_desktop)

        startmenu_paths = [
            Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs")
        ]

        for path in desktop_paths + startmenu_paths:
            shortcuts.extend(path.glob("*.lnk"))
        return shortcuts

    def get_shortcut_info(self, shortcut_path):
        """获取快捷方式信息"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))

            return {
                'name': shortcut_path.stem,
                'path': str(shortcut_path),
                'target': shortcut.Targetpath,
                'icon': shortcut.IconLocation,
                'working_dir': shortcut.WorkingDirectory
            }
        except Exception as e:
            return None

    def find_matching_icon(self, app_name):
        """查找匹配的图标文件"""
        if not self.icon_folder:
            return None

        icon_folder = Path(self.icon_folder)
        app_name_clean = app_name.lower().replace(" ", "").replace("-", "").replace("_", "")

        # 查找完全匹配
        for ext in self.supported_formats:
            for name_variant in [app_name, app_name.replace(" ", ""), app_name.replace(" ", "_"),
                                 app_name.replace(" ", "-")]:
                exact_match = icon_folder / f"{name_variant}{ext}"
                if exact_match.exists():
                    return str(exact_match)

        # 模糊匹配
        for icon_file in icon_folder.iterdir():
            if icon_file.suffix.lower() in self.supported_formats:
                icon_name_clean = icon_file.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
                if app_name_clean in icon_name_clean or icon_name_clean in app_name_clean:
                    return str(icon_file)

        return None

    def scan_applications(self):
        """扫描应用程序"""
        if not self.icon_folder:
            messagebox.showerror("错误", "请先选择图标文件夹")
            return

        self.progress_var.set("正在扫描应用程序...")
        self.tree.delete(*self.tree.get_children())

        def scan_thread():
            try:
                shortcuts = self.get_shortcuts()
                processed_names = set()

                for i, shortcut in enumerate(shortcuts):
                    info = self.get_shortcut_info(shortcut)
                    if not info or not info['target']:
                        continue

                    # 避免重复
                    if info['name'].lower() in processed_names:
                        continue
                    processed_names.add(info['name'].lower())

                    # 查找匹配的图标
                    matching_icon = self.find_matching_icon(info['name'])
                    status = "有匹配图标" if matching_icon else "无匹配"
                    icon_display = Path(matching_icon).name if matching_icon else "无匹配"

                    # 添加到表格
                    self.root.after(0, lambda i=info, mi=icon_display, s=status:
                    self.tree.insert('', 'end', values=(
                        "", i['name'], i['path'], i['target'], mi, s
                    )))

                    # 更新进度
                    if i % 10 == 0:  # 每10个更新一次进度
                        progress = f"扫描中... {i}/{len(shortcuts)}"
                        self.root.after(0, lambda p=progress: self.progress_var.set(p))

                matched_count = len([item_id for item_id in self.tree.get_children()
                                     if self.tree.item(item_id)['values'][5] == "有匹配图标"])

                self.root.after(0, lambda: self.progress_var.set(
                    f"扫描完成! 找到 {len(processed_names)} 个应用，其中 {matched_count} 个有匹配图标"))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {str(e)}"))
                self.root.after(0, lambda: self.progress_var.set("扫描失败"))

        threading.Thread(target=scan_thread, daemon=True).start()

    def create_backup_folder(self):
        """创建备份文件夹"""
        if not self.backup_folder:
            self.backup_folder = Path.home() / "Desktop" / "快捷方式图标备份"
            self.backup_folder.mkdir(exist_ok=True)
        return self.backup_folder

    def convert_to_ico(self, image_path, output_path):
        """将其他格式图片转换为ICO格式"""
        try:
            with Image.open(image_path) as img:
                # 确保是RGBA模式
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # 调整大小到标准图标尺寸
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
                img_list = []

                for size in sizes:
                    resized_img = img.resize(size, Image.Resampling.LANCZOS)
                    img_list.append(resized_img)

                # 保存为ICO格式
                img_list[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in img_list])
                return True
        except Exception as e:
            print(f"转换图标失败: {e}")
            return False

    def backup_shortcut(self, shortcut_path):
        """备份快捷方式"""
        try:
            backup_folder = self.create_backup_folder()
            backup_path = backup_folder / Path(shortcut_path).name

            # 如果备份已存在，添加数字后缀
            counter = 1
            original_backup_path = backup_path
            while backup_path.exists():
                backup_path = original_backup_path.with_stem(f"{original_backup_path.stem}_{counter}")
                counter += 1

            shutil.copy2(shortcut_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"备份失败: {e}")
            return None

    def replace_shortcut_icon(self, shortcut_path, icon_path):
        """替换指定快捷方式的图标"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.IconLocation = icon_path
            shortcut.save()

            # 刷新图标缓存（可选）
            from ctypes import windll
            windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)

            return True, "替换成功"
        except PermissionError:
            return False, "权限不足"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def replace_selected_icons(self):
        """替换选中的图标"""
        selected_items = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id)['values']
            if values[0] == "√" and values[5] == "有匹配图标":
                selected_items.append((item_id, values))

        if not selected_items:
            messagebox.showwarning("警告", "请先选择要替换的应用程序（双击行来选择）")
            return

        # 确认操作
        result = messagebox.askyesno("确认操作",
                                     f"确定要替换 {len(selected_items)} 个应用程序的图标吗？")
        if not result:
            return

        def replace_thread():
            success_count = 0

            for i, (item_id, values) in enumerate(selected_items):
                app_name = values[1]
                shortcut_path = values[2]
                icon_name = values[4]

                try:
                    # 更新状态
                    self.root.after(0, lambda iid=item_id: self.update_item_status(iid, "正在处理..."))

                    # 查找完整的图标路径
                    icon_path = None
                    icon_folder = Path(self.icon_folder)
                    for icon_file in icon_folder.iterdir():
                        if icon_file.name == icon_name:
                            icon_path = str(icon_file)
                            break

                    if not icon_path:
                        self.root.after(0, lambda iid=item_id: self.update_item_status(iid, "图标文件未找到"))
                        continue

                    # 备份原快捷方式
                    backup_path = None
                    if self.backup_var.get():
                        backup_path = self.backup_shortcut(shortcut_path)
                        if not backup_path:
                            self.root.after(0, lambda iid=item_id: self.update_item_status(iid, "备份失败"))
                            continue

                    # 替换图标
                    success, message = self.replace_shortcut_icon(shortcut_path, icon_path)

                    if success:
                        success_count += 1
                        self.root.after(0, lambda iid=item_id: self.update_item_status(iid, "✓ 替换成功"))
                    else:
                        self.root.after(0, lambda iid=item_id, msg=message:
                        self.update_item_status(iid, f"✗ {msg}"))

                except Exception as e:
                    self.root.after(0, lambda iid=item_id, err=str(e):
                    self.update_item_status(iid, f"✗ 错误: {err}"))

                # 更新总进度
                progress = f"进度: {i + 1}/{len(selected_items)} - 成功: {success_count}"
                self.root.after(0, lambda p=progress: self.progress_var.set(p))

            # 完成提示
            final_msg = f"替换完成! 成功替换了 {success_count}/{len(selected_items)} 个图标"
            self.root.after(0, lambda: self.progress_var.set(final_msg))

            if success_count > 0:
                self.root.after(0, lambda: messagebox.showinfo("完成",
                                                               f"{final_msg}\n\n原快捷方式已备份到桌面的'快捷方式图标备份'文件夹中。\n"
                                                               f"如需恢复，可使用'恢复备份'功能。"))

        threading.Thread(target=replace_thread, daemon=True).start()

    def update_item_status(self, item_id, status):
        """更新列表项状态"""
        values = list(self.tree.item(item_id)['values'])
        values[5] = status
        self.tree.item(item_id, values=values)

    def restore_backup(self):
        """恢复备份"""
        backup_folder = Path.home() / "Desktop" / "快捷方式图标备份"
        if not backup_folder.exists() or not list(backup_folder.iterdir()):
            messagebox.showinfo("信息", "没有找到备份文件")
            return

        backup_files = list(backup_folder.glob("*.lnk"))
        if not backup_files:
            messagebox.showinfo("信息", "备份文件夹中没有快捷方式文件")
            return

        # 让用户选择要恢复的备份文件
        restore_window = tk.Toplevel(self.root)
        restore_window.title("选择要恢复的备份")
        restore_window.geometry("500x400")

        ttk.Label(restore_window, text="选择要恢复的备份文件:").pack(pady=10)

        # 创建列表框
        listbox_frame = ttk.Frame(restore_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
        scrollbar_restore = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar_restore.set)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_restore.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加备份文件到列表
        for backup_file in backup_files:
            listbox.insert(tk.END, backup_file.name)

        # 按钮框架
        btn_frame = ttk.Frame(restore_window)
        btn_frame.pack(pady=10)

        def do_restore():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("警告", "请选择要恢复的备份文件")
                return

            success_count = 0
            for index in selected_indices:
                backup_file = backup_files[index]
                # 确定原始位置（这里简化处理，恢复到桌面）
                original_path = Path.home() / "Desktop" / backup_file.name
                try:
                    shutil.copy2(backup_file, original_path)
                    success_count += 1
                except Exception as e:
                    print(f"恢复 {backup_file.name} 失败: {e}")

            messagebox.showinfo("完成", f"成功恢复了 {success_count} 个快捷方式到桌面")
            restore_window.destroy()

        ttk.Button(btn_frame, text="恢复选中项", command=do_restore).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=restore_window.destroy).pack(side=tk.LEFT, padx=5)

    def run(self):
        """运行程序"""
        self.root.mainloop()
class InfoDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.result = False
        self.dont_show_var = tk.BooleanVar(value=False)
        self.title(title)
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        label = ttk.Label(self, text=message, wraplength=380, justify=tk.LEFT)
        label.pack(padx=10, pady=10, anchor=tk.W)

        chk = ttk.Checkbutton(self, text="不再显示此提示", variable=self.dont_show_var)
        chk.pack(padx=10, pady=(0, 10), anchor=tk.W)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ok_btn = ttk.Button(btn_frame, text="确定", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window()

    def on_ok(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()

def main():
    # 1) 依赖检查
    try:
        import win32com.client
        from PIL import Image
    except ImportError as e:
        missing = ['pywin32'] if 'win32com' in str(e) else []
        if 'PIL' in str(e):
            missing.append('Pillow')
        ctypes.windll.user32.MessageBoxW(
            0,
            f"请先安装依赖：\npip install {' '.join(missing)}",
            "缺少依赖包",
            0x10)
        return
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, str(e), "启动失败", 0x10)
        return

    # 2) 管理员提权
    if not is_user_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 0)
        return

    # 3) 带复选框的系统欢迎框
    flag_path = Path(tempfile.gettempdir()) / ".icon_replacer_dont_show"

    # 用 taskdialog 实现真正的“下次不再显示”复选框
    TASKDIALOG_BUTTON_OK = 1
    TASKDIALOG_BUTTON_CANCEL = 2
    TDCBF_YES_BUTTON = 0x0100
    TDCBF_NO_BUTTON = 0x0004

    # 简单做法：先弹普通 Yes/No，再追加一个 Checkbox
    # 这里用 MessageBox + 手动写标记文件
    if not flag_path.exists():
        result = ctypes.windll.user32.MessageBoxW(
            0,
            "这个工具可以批量替换桌面和开始菜单中应用程序的图标。\n\n"
            "使用前请确保：\n"
            "1. 已准备好图标文件（建议使用.ico格式）\n"
            "2. 图标文件名与应用程序名称对应\n"
            "3. 关闭要替换图标的应用程序\n\n"
            "程序可选择备份原始快捷方式。\n\n"
            "是否继续？",
            "桌面图标替换工具",
            0x24)  # 0x24 = MB_YESNO | MB_ICONQUESTION
        if result != 6:          # 6 = IDYES
            return
        # 再弹一次复选框
        checkbox = ctypes.windll.user32.MessageBoxW(
            0,
            "是否下次启动时不再显示此提示？",
            "提示",
            0x23)  # 0x23 = MB_YESNO | MB_ICONQUESTION
        if checkbox == 6:
            flag_path.touch()

    # 4) 进入主程序
    app = IconReplacer()
    app.run()


if __name__ == "__main__":
    main()