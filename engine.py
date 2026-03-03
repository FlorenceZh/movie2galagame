import statistics
import pathlib
import subprocess
import datetime

import cv2
import pysrt
from rapidocr_onnxruntime import RapidOCR
from moviepy import VideoFileClip


def format_time(seconds: float) -> str:
    """将秒数格式化为 SRT 的时间字符串：HH:MM:SS,mmm"""
    delta = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds_int = divmod(remainder, 60)
    milliseconds = int(delta.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"

def calculate_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的简单相似度，判断是否为同一段字幕"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    # 采用 Jaccard 相似度简单实现
    set1, set2 = set(s1), set(s2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


class Engine:
    __SCRIPT_BLOCK_TEMPLATE = '''
    show b{id} with dissolve\n
    voice a{id}\n
    "{text}"
    '''

    __SCRIPT_TEMPLATE = '''#该脚本由 https://github.com/FlorenceZh/movie2galagame 生成
label start:
{script_block}
    return
'''

    def __init__(self, video_path: str, srt_path: str = None, output_folder: str = 'output') -> None:
        self.base_path = pathlib.Path(output_folder)
        self.__video_path = pathlib.Path(video_path)

        (self.base_path / 'images').mkdir(parents=True, exist_ok=True)
        (self.base_path / 'audio').mkdir(parents=True, exist_ok=True)

        if not srt_path:
            self.__srt_path = self.base_path / 'extracted.srt'
            # 1. 尝试使用 ffmpeg 提取内嵌字幕
            cmd = ['ffmpeg', '-y', '-i', str(self.__video_path), '-map', '0:s:0', str(self.__srt_path)]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            # 2. 如果提取失败或文件为空，回退到 OCR 提取硬字幕
            if not self.__srt_path.exists() or self.__srt_path.stat().st_size == 0:
                print("未检测到内嵌字幕，正在使用 OCR 提取硬字幕，请耐心等待...")
                self.__extract_hard_subtitles(str(self.__video_path), str(self.__srt_path))
        else:
            self.__srt_path = pathlib.Path(srt_path)

        self.__subs = pysrt.open(self.__srt_path) # type: ignore
        self.__script_blocks = []

    def __extract_hard_subtitles(self, video_path: str, output_srt: str):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 为了提高效率，我们每半秒采样一次
        sample_interval = max(1, int(fps / 2))

        engine = RapidOCR()

        subtitles = []
        current_sub = None

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                h, w, _ = frame.shape
                # 截取底部 30% 画面
                crop = frame[int(h * 0.7):h, 0:w]
                result, _ = engine(crop)

                text = ""
                if result:
                    # 组合识别出的所有文本块
                    text = " ".join([res[1] for res in result]).strip()

                current_time = frame_idx / fps

                if text:
                    # 存在字幕文本
                    if current_sub is None:
                        # 新字幕块
                        current_sub = {'text': text, 'start': current_time, 'end': current_time + (sample_interval / fps)}
                    else:
                        # 检查相似度决定是否合并
                        if calculate_similarity(current_sub['text'], text) > 0.6:
                            current_sub['end'] = current_time + (sample_interval / fps)
                            # 如果新的文本更长，可能识别更完整，更新文本
                            if len(text) > len(current_sub['text']):
                                current_sub['text'] = text
                        else:
                            # 相似度过低，认为是新字幕
                            subtitles.append(current_sub)
                            current_sub = {'text': text, 'start': current_time, 'end': current_time + (sample_interval / fps)}
                else:
                    # 不存在字幕文本，闭合当前的字幕块
                    if current_sub is not None:
                        subtitles.append(current_sub)
                        current_sub = None
            frame_idx += 1

        if current_sub is not None:
            subtitles.append(current_sub)

        cap.release()

        # 写入 SRT 文件
        with open(output_srt, 'w', encoding='utf-8') as f:
            for idx, sub in enumerate(subtitles, start=1):
                start_str = format_time(sub['start'])
                end_str = format_time(sub['end'])
                f.write(f"{idx}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{sub['text']}\n\n")

    def process(self):
        with VideoFileClip(str(self.__video_path)) as video_clip:
            for index, sub in enumerate(self.__subs):
                # 统一单位为秒
                start = sub.start.ordinal / 1000.0
                end = sub.end.ordinal / 1000.0
                
                self.__process_frame(video_clip, index, start, end)
                self.__process_audio(video_clip, index, start, end)
                self.__generate_every_script_block(index, sub)

            full_script = self.__SCRIPT_TEMPLATE.format(
                script_block="".join(self.__script_blocks)
            )
            
            # 3. 将 script.rpy 写入 output 文件夹
            script_file_path = self.base_path / 'script.rpy'
            with open(script_file_path, mode='w', encoding='utf-8') as f:
                f.write(full_script)
            
            print(f"处理完成！所有文件已保存在: {self.base_path.absolute()}")

    def __process_frame(self, clip, current_id: int, start: float, end: float):
        frame_time = statistics.mean((start, end))
        # 4. 使用 base_path 拼接路径
        save_path = self.base_path / "images" / f"b{current_id}.jpg"
        clip.save_frame(save_path, t=frame_time)

    def __process_audio(self, clip, current_id: int, start: float, end: float):
        # 修正：moviepy 的 subclipped 接受秒为单位
        audio_clip = clip.audio.subclipped(start, end)
        try:
            # 5. 使用 base_path 拼接路径
            save_path = self.base_path / "audio" / f"a{current_id}.mp3"
            audio_clip.write_audiofile(save_path, logger=None)
        except Exception as e:
            print(f'警告：索引 {current_id} 音频提取失败: {e}')

    def __generate_every_script_block(self, current_id: int, sub):
        code_block = self.__SCRIPT_BLOCK_TEMPLATE.format(
            id=current_id, 
            text=sub.text.replace('\n', ' ')
        )
        self.__script_blocks.append(code_block)


if __name__ == '__main__':
    engine = Engine('测试-新海诚_十字路口.mp4', '测试-新海诚_十字路口.srt', output_folder='output')
    engine.process()