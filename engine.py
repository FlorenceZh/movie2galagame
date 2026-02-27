import statistics
import pathlib

import pysrt
from moviepy import VideoFileClip


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

    def __init__(self, video_path: str, srt_path: str, output_folder: str = 'output') -> None:
        self.base_path = pathlib.Path(output_folder)
        self.__video_path = pathlib.Path(video_path)
        self.__srt_path = pathlib.Path(srt_path)

        (self.base_path / 'images').mkdir(parents=True, exist_ok=True)
        (self.base_path / 'audio').mkdir(parents=True, exist_ok=True)

        self.__subs = pysrt.open(self.__srt_path) # type: ignore
        self.__script_blocks = []

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