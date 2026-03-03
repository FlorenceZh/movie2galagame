import os
import pathlib
import pytest

from engine import Engine

def test_engine_with_ocr_extraction(tmp_path):
    # This assumes `测试-新海诚_十字路口.mp4` exists in the repo root
    # and has a hardcoded subtitle track.
    video_path = pathlib.Path('测试-新海诚_十字路口.mp4').resolve()

    # Check if the test file actually exists; if not, just skip the test.
    if not video_path.exists():
        pytest.skip("Test video file not found.")

    output_dir = tmp_path / "output"

    # Initialize Engine with None for srt_path
    engine = Engine(str(video_path), srt_path=None, output_folder=str(output_dir))

    # Verify that the extracted.srt file was created
    extracted_srt = output_dir / "extracted.srt"
    assert extracted_srt.exists()
    assert extracted_srt.stat().st_size > 0

    # Verify the contents of extracted srt are somewhat populated
    with open(extracted_srt, 'r', encoding='utf-8') as f:
        content = f.read()
        # Should contain standard SRT formatting things like "-->"
        assert "-->" in content

    # Process the video
    engine.process()

    # Verify that images and audio directories exist and contain files
    images_dir = output_dir / "images"
    audio_dir = output_dir / "audio"
    script_file = output_dir / "script.rpy"

    assert images_dir.exists()
    assert audio_dir.exists()
    assert script_file.exists()

    # We should have at least some jpg and mp3 files generated if subs were not empty
    images = list(images_dir.glob("*.jpg"))
    audios = list(audio_dir.glob("*.mp3"))

    assert len(images) > 0
    assert len(audios) > 0
