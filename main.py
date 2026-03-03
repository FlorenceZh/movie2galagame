import os
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from engine import Engine


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("movie2galagame")
        self.geometry("560x320")
        self.resizable(False, False)

        self._video_path = tk.StringVar()
        self._srt_path = tk.StringVar()
        self._output_dir = tk.StringVar(value="output")
        self._progress = None

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 8}

        title = tk.Label(self, text="movie2galagame 转换工具", font=("Segoe UI", 14, "bold"))
        title.pack(**pad)

        form = tk.Frame(self)
        form.pack(fill="x", **pad)

        self._row(form, "视频文件 (.mp4)", self._video_path, self._choose_video)
        self._row(form, "字幕文件 (.srt)", self._srt_path, self._choose_srt)
        self._row(form, "输出目录", self._output_dir, self._choose_output)

        actions = tk.Frame(self)
        actions.pack(fill="x", **pad)

        self._run_btn = tk.Button(actions, text="开始转换", command=self._run, width=16)
        self._run_btn.pack(side="right")

        self._progress = ttk.Progressbar(actions, mode="indeterminate")
        self._progress.pack(side="left", fill="x", expand=True, padx=6)

        hint = tk.Label(self, text="提示：请先选择视频与字幕文件，再开始转换。")
        hint.pack(**pad)

    def _row(self, parent, label_text, var, browse_cmd) -> None:
        row = tk.Frame(parent)
        row.pack(fill="x", pady=6)

        label = tk.Label(row, text=label_text, width=14, anchor="w")
        label.pack(side="left")

        entry = tk.Entry(row, textvariable=var)
        entry.pack(side="left", fill="x", expand=True, padx=6)

        btn = tk.Button(row, text="浏览", command=browse_cmd, width=8)
        btn.pack(side="right")

    def _pick_path(self, var, title, is_dir=False, filetypes=None) -> None:
        if is_dir:
            path = filedialog.askdirectory(title=title)
        else:
            path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir=os.getcwd(),
            )
        if path:
            var.set(path)

    def _choose_video(self) -> None:
        self._pick_path(
            self._video_path,
            "选择视频文件",
            filetypes=[("视频文件", "*.mp4"), ("所有文件", "*.*")],
        )

    def _choose_srt(self) -> None:
        self._pick_path(
            self._srt_path,
            "选择字幕文件",
            filetypes=[("字幕文件", "*.srt"), ("所有文件", "*.*")],
        )

    def _choose_output(self) -> None:
        self._pick_path(self._output_dir, "选择输出目录", is_dir=True)

    def _run(self) -> None:
        video = self._video_path.get().strip()
        srt = self._srt_path.get().strip()
        out_dir = self._output_dir.get().strip() or "output"

        if not video or not srt:
            messagebox.showwarning("缺少文件", "请先选择视频文件和字幕文件。")
            return

        self._run_btn.config(state="disabled")
        self._progress.start(8)
        self.update_idletasks()
        try:
            engine = Engine(video, srt, output_folder=out_dir)
            engine.process()
        except Exception as exc:
            self._progress.stop()
            self._run_btn.config(state="normal")
            messagebox.showerror("转换失败", f"发生错误：{exc}")
            return

        self._progress.stop()
        self._run_btn.config(state="normal")
        output_path = pathlib.Path(out_dir).resolve()
        messagebox.showinfo("完成", f"转换完成，输出目录：\n{output_path}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
