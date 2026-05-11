#!/usr/bin/env python3
"""文件整理工具 - 一键按类别整理文件到文件夹"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CATEGORIES = {
    "图片": ("图片", {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".heic", ".raw", ".psd", ".ai"}),
    "视频": ("视频", {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ts", ".rmvb"}),
    "音频": ("音频", {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".mid"}),
    "文档": ("文档", {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt", ".csv", ".md", ".epub", ".mobi"}),
    "压缩包": ("压缩包", {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".cab", ".lzma"}),
    "代码": ("代码", {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".rb", ".php", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".bat", ".lua"}),
    "安装包": ("安装包", {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk", ".appx"}),
}


class FileOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("文件整理工具")
        self.root.geometry("620x520")
        self.root.resizable(False, False)

        self.folder_path = tk.StringVar(value=os.getcwd())
        self.category_vars = {}
        self.file_groups = {}

        self._build_ui()
        self._scan_files()

    def _build_ui(self):
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="目标文件夹:").pack(side="left")
        ttk.Entry(frame_top, textvariable=self.folder_path, width=50).pack(side="left", padx=5)
        ttk.Button(frame_top, text="选择", command=self._choose_folder).pack(side="left")
        ttk.Button(frame_top, text="刷新", command=self._scan_files).pack(side="left", padx=5)

        frame_mid = ttk.LabelFrame(self.root, text="选择要整理的类别", padding=10)
        frame_mid.pack(fill="x", padx=10, pady=5)

        col = 0
        row = 0
        for name in CATEGORIES:
            var = tk.BooleanVar(value=True)
            self.category_vars[name] = var
            cb = ttk.Checkbutton(frame_mid, text=name, variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=12, pady=3)
            lbl = ttk.Label(frame_mid, text=" (0)")
            lbl.grid(row=row, column=col + 1, sticky="w")
            self.category_vars[name + "_label"] = lbl
            col += 2
            if col >= 6:
                col = 0
                row += 1

        frame_btn = ttk.Frame(self.root, padding=(10, 5))
        frame_btn.pack(fill="x")
        ttk.Button(frame_btn, text="全选", command=self._select_all).pack(side="left")
        ttk.Button(frame_btn, text="全不选", command=self._select_none).pack(side="left", padx=5)
        ttk.Button(frame_btn, text="开始整理", command=self._organize).pack(side="right")

        frame_list = ttk.LabelFrame(self.root, text="文件预览", padding=5)
        frame_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(frame_list, columns=("文件名", "类别"), show="headings", height=12)
        self.tree.heading("文件名", text="文件名")
        self.tree.heading("类别", text="类别")
        self.tree.column("文件名", width=440)
        self.tree.column("类别", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", padding=5).pack(fill="x", padx=10, pady=(0, 8))

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)
            self._scan_files()

    def _scan_files(self):
        path = self.folder_path.get()
        self.file_groups = {name: [] for name in CATEGORIES}
        self.file_groups["其他"] = []
        ext_map = {}
        for name, (_, exts) in CATEGORIES.items():
            for ext in exts:
                ext_map[ext] = name

        try:
            entries = os.listdir(path)
        except OSError as e:
            messagebox.showerror("错误", f"无法读取文件夹:\n{e}")
            return

        for f in entries:
            full = os.path.join(path, f)
            if not os.path.isfile(full):
                continue
            ext = os.path.splitext(f)[1].lower()
            cat = ext_map.get(ext, "其他")
            self.file_groups[cat].append(f)

        for name in CATEGORIES:
            lbl = self.category_vars.get(name + "_label")
            if lbl:
                lbl.config(text=f" ({len(self.file_groups.get(name, []))})")

        total = sum(len(v) for v in self.file_groups.values())
        self.status_var.set(f"扫描完成: 找到 {total} 个文件")

        for item in self.tree.get_children():
            self.tree.delete(item)
        for cat, files in self.file_groups.items():
            for f in sorted(files):
                self.tree.insert("", "end", values=(f, cat))

    def _select_all(self):
        for name in CATEGORIES:
            self.category_vars[name].set(True)

    def _select_none(self):
        for name in CATEGORIES:
            self.category_vars[name].set(False)

    def _organize(self):
        path = self.folder_path.get()
        selected = [name for name in CATEGORIES if self.category_vars[name].get()]

        if not selected:
            messagebox.showinfo("提示", "请至少选择一个类别")
            return

        total = 0
        errors = []
        for cat in selected:
            folder_name = CATEGORIES[cat][0]
            target_dir = os.path.join(path, folder_name)
            files = self.file_groups.get(cat, [])
            if not files:
                continue
            os.makedirs(target_dir, exist_ok=True)
            for f in files:
                src = os.path.join(path, f)
                dst = os.path.join(target_dir, f)
                if os.path.exists(dst):
                    name, ext = os.path.splitext(f)
                    i = 1
                    while os.path.exists(dst):
                        dst = os.path.join(target_dir, f"{name}_{i}{ext}")
                        i += 1
                try:
                    shutil.move(src, dst)
                    total += 1
                except Exception as e:
                    errors.append(f"{f}: {e}")

        msg = f"整理完成! 共移动 {total} 个文件"
        if errors:
            msg += f"\n\n{len(errors)} 个文件失败:\n" + "\n".join(errors[:5])
        messagebox.showinfo("结果", msg)
        self._scan_files()


def main():
    root = tk.Tk()
    FileOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
