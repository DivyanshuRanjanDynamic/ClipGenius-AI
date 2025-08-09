import glob
import json
import pathlib 
import pickle
import shutil
import subprocess
import time
import boto3
import uuid
import cv2
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import ffmpegcv
import modal
import numpy as np
from pydantic import BaseModel
import os
import pysubs2
from tqdm import tqdm
import whisperx
from pathlib import Path
import requests
from boto3.s3.transfer import TransferConfig
import concurrent.futures
import google.generativeai as genai
import argparse

class ProcessVideoRequest(BaseModel):
    s3_key: str

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.12"
    )
    .apt_install(["ffmpeg", "libgl1-mesa-glx", "wget", "libcudnn8", "libcudnn8-dev"])
    .pip_install_from_requirements("requirements.txt")
    .run_commands([
    "mkdir -p /usr/share/fonts/truetype/custom",
    "wget -O /usr/share/fonts/truetype/custom/Anton-Regular.ttf https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
   # "wget -O /usr/share/fonts/truetype/custom/NotoSans-Regular.ttf https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
    "fc-cache -f -v",])
    .add_local_dir("fonts", "/usr/share/fonts/truetype/custom", copy=True)  
    .add_local_dir("LR-ASD", "/LR-ASD", copy=True)
)

app = modal.App("ai-SAAS", image=image)

volume = modal.Volume.from_name(
    "ai-SAAS-model-cache", create_if_missing=True
)

mount_path = "/root/.cache/torch"

auth_scheme = HTTPBearer()

def run_subprocess(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, **kwargs)
        return result
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Subprocess failed: {cmd}")
        print(f"[STDERR]\n{e.stderr}")
        raise

def create_vertical_video(tracks, scores, pyframes_path, pyavi_path, audio_path, output_path, framerate=25):
    target_width = 1080
    target_height = 1920

    flist = glob.glob(os.path.join(pyframes_path, "*.jpg"))
    flist.sort()

    faces = [[] for _ in range(len(flist))]

    for tidx, track in enumerate(tracks):
        score_array = scores[tidx]
        for fidx, frame in enumerate(track["track"]["frame"].tolist()):
            slice_start = max(fidx - 30, 0)
            slice_end = min(fidx + 30, len(score_array))
            score_slice = score_array[slice_start:slice_end]
            avg_score = float(np.mean(score_slice)
                              if len(score_slice) > 0 else 0)

            faces[frame].append(
                {'track': tidx, 'score': avg_score, 's': track['proc_track']["s"][fidx], 'x': track['proc_track']["x"][fidx], 'y': track['proc_track']["y"][fidx]})

    temp_video_path = os.path.join(pyavi_path, "video_only.mp4")

    vout = None
    for fidx, fname in tqdm(enumerate(flist), total=len(flist), desc="Creating vertical video"):
        img = cv2.imread(fname)
        if img is None:
            continue

        current_faces = faces[fidx]

        max_score_face = max(
            current_faces, key=lambda face: face['score']) if current_faces else None

        if max_score_face and max_score_face['score'] < 0:
            max_score_face = None

        if vout is None:
            vout = ffmpegcv.VideoWriterNV(
                file=temp_video_path,
                codec=None,
                fps=framerate,
                resize=(target_width, target_height)
            )

        if max_score_face:
            mode = "crop"
        else:
            mode = "resize"

        if mode == "resize":
            scale = target_width / img.shape[1]
            resized_height = int(img.shape[0] * scale)
            resized_image = cv2.resize(
                img, (target_width, resized_height), interpolation=cv2.INTER_AREA)

            scale_for_bg = max(
                target_width / img.shape[1], target_height / img.shape[0])
            bg_width = int(img.shape[1] * scale_for_bg)
            bg_heigth = int(img.shape[0] * scale_for_bg)

            blurred_background = cv2.resize(img, (bg_width, bg_heigth))
            blurred_background = cv2.GaussianBlur(
                blurred_background, (121, 121), 0)

            crop_x = (bg_width - target_width) // 2
            crop_y = (bg_heigth - target_height) // 2
            blurred_background = blurred_background[crop_y:crop_y +
                                                    target_height, crop_x:crop_x + target_width]

            center_y = (target_height - resized_height) // 2
            blurred_background[center_y:center_y +
                               resized_height, :] = resized_image

            vout.write(blurred_background)

        elif mode == "crop":
            scale = target_height / img.shape[0]
            resized_image = cv2.resize(
                img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            frame_width = resized_image.shape[1]

            center_x = int(
                max_score_face["x"] * scale if max_score_face else frame_width // 2)
            top_x = max(min(center_x - target_width // 2,
                        frame_width - target_width), 0)

            image_cropped = resized_image[0:target_height,
                                          top_x:top_x + target_width]

            vout.write(image_cropped)

    if vout:
        vout.release()

    # Use fast preset, reasonable bitrate, and hardware acceleration if available
    ffmpeg_codec = "-c:v h264_nvenc" if shutil.which("nvidia-smi") else "-c:v libx264"
    ffmpeg_command = (f"ffmpeg -y -hwaccel auto -i {temp_video_path} -i {audio_path} "
                      f"{ffmpeg_codec} -preset fast -b:v 1M -c:a aac -b:a 128k "
                      f"{output_path}")
    run_subprocess(ffmpeg_command)


def create_subtitles_with_ffmpeg(transcript_segments: list, clip_start: float, clip_end: float, clip_video_path: str, output_path: str, max_words: int = 5, fontsize: int = 140):
    temp_dir = os.path.dirname(output_path)
    subtitle_path = os.path.join(temp_dir, "temp_subtitles.ass")

    clip_segments = [segment for segment in transcript_segments
                     if segment.get("start") is not None
                     and segment.get("end") is not None
                     and segment.get("end") > clip_start
                     and segment.get("start") < clip_end
                     ]

    subtitles = []
    current_words = []
    current_start = None
    current_end = None

    for segment in clip_segments:
        word = segment.get("word", "").strip()
        seg_start = segment.get("start")
        seg_end = segment.get("end")

        if not word or seg_start is None or seg_end is None:
            continue

        start_rel = max(0.0, seg_start - clip_start)
        end_rel = max(0.0, seg_end - clip_start)

        if end_rel <= 0:
            continue

        if not current_words:
            current_start = start_rel
            current_end = end_rel
            current_words = [word]
        elif len(current_words) >= max_words:
            subtitles.append(
                (current_start, current_end, ' '.join(current_words)))
            current_words = [word]
            current_start = start_rel
            current_end = end_rel
        else:
            current_words.append(word)
            current_end = end_rel

    if current_words:
        subtitles.append(
            (current_start, current_end, ' '.join(current_words)))

    subs = pysubs2.SSAFile()

    subs.info["WrapStyle"] = 0
    subs.info["ScaledBorderAndShadow"] = "yes"
    subs.info["PlayResX"] = 1080
    subs.info["PlayResY"] = 1920
    subs.info["ScriptType"] = "v4.00+"

    style_name = "Default"
    new_style = pysubs2.SSAStyle()
    new_style.fontname = "Anton"
    new_style.fontsize = fontsize
    new_style.primarycolor = pysubs2.Color(255, 255, 255)
    new_style.outline = 2.0
    new_style.shadow = 2.0
    new_style.shadowcolor = pysubs2.Color(0, 0, 0, 128)
    new_style.alignment = 2
    new_style.marginl = 50
    new_style.marginr = 50
    new_style.marginv = 50
    new_style.spacing = 0.0

    subs.styles[style_name] = new_style

    for i, (start, end, text) in enumerate(subtitles):
        start_time = pysubs2.make_time(s=start)
        end_time = pysubs2.make_time(s=end)
        line = pysubs2.SSAEvent(
            start=start_time, end=end_time, text=text, style=style_name)
        subs.events.append(line)

    subs.save(subtitle_path)

    ffmpeg_cmd = (f"ffmpeg -y -i {clip_video_path} -vf \"ass={subtitle_path}\" "
                  f"-c:v h264 -preset fast -crf 23 {output_path}")

    subprocess.run(ffmpeg_cmd, shell=True, check=True)

def process_clip(base_dir, original_video_path, s3_key, start_time, end_time, clip_index, transcript_words, audio_sample_rate=16000, audio_channels=1, subtitle_max_words=5, subtitle_fontsize=140, debug=False):
    """
    Processes a single viral clip:
    - Extracts the segment
    - Runs LR-ASD for active speaker detection
    - Creates a vertical video focusing on the speaker
    - Adds subtitles
    - Uploads to S3
    """
    clip_name = f"clip_{clip_index}"
    s3_key_dir = os.path.dirname(s3_key)
    output_s3_key = f"{s3_key_dir}/{clip_name}.mp4"
    print(f"Output S3 key: {output_s3_key}")

    clip_dir = base_dir / clip_name
    clip_dir.mkdir(parents=True, exist_ok=True)

    clip_segment_path = clip_dir / f"{clip_name}_segment.mp4"
    vertical_mp4_path = clip_dir / "pyavi" / "video_out_vertical.mp4"
    subtitle_output_path = clip_dir / "pyavi" / "video_with_subtitles.mp4"

    (clip_dir / "pywork").mkdir(exist_ok=True)
    pyframes_path = clip_dir / "pyframes"
    pyavi_path = clip_dir / "pyavi"
    audio_path = clip_dir / "pyavi" / "audio.wav"

    pyframes_path.mkdir(exist_ok=True)
    pyavi_path.mkdir(exist_ok=True)

    duration = end_time - start_time
    # Use fast preset, reasonable bitrate, and hardware acceleration if available
    ffmpeg_codec = "-c:v h264_nvenc" if shutil.which("nvidia-smi") else "-c:v libx264"
    cut_command = (f"ffmpeg -y -hwaccel auto -i \"{original_video_path}\" -ss {start_time} -t {duration} "
                   f"{ffmpeg_codec} -preset fast -b:v 1M -c:a aac -b:a 128k \"{clip_segment_path}\"")
    run_subprocess(cut_command)

    extract_cmd = f"ffmpeg -y -i \"{clip_segment_path}\" -vn -acodec pcm_s16le -ar {audio_sample_rate} -ac {audio_channels} \"{audio_path}\""
    run_subprocess(extract_cmd)

    shutil.copy(clip_segment_path, base_dir / f"{clip_name}.mp4")

    # --- LR-ASD: Active Speaker Detection ---
    columbia_command = (f"python Columbia_test.py --videoName {clip_name} "
                        f"--videoFolder {str(base_dir)} "
                        f"--pretrainModel weight/finetuning_TalkSet.model")
    run_subprocess(columbia_command, cwd="LR-ASD")

    tracks_path = clip_dir / "pywork" / "tracks.pckl"
    scores_path = clip_dir / "pywork" / "scores.pckl"
    if not tracks_path.exists() or not scores_path.exists():
        raise FileNotFoundError("Tracks or scores not found for clip")

    with open(tracks_path, "rb") as f:
        tracks = pickle.load(f)
    with open(scores_path, "rb") as f:
        scores = pickle.load(f)

    # --- Create vertical video focusing on active speaker ---
    create_vertical_video(
        tracks, scores, pyframes_path, pyavi_path, audio_path, vertical_mp4_path
    )

    # --- Generate subtitles for the clip ---
    create_subtitles_with_ffmpeg(
        transcript_words, start_time, end_time, vertical_mp4_path, subtitle_output_path, max_words=subtitle_max_words, fontsize=subtitle_fontsize
    )

    # --- Upload to S3 ---
    file_size = os.path.getsize(str(subtitle_output_path))
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    config = TransferConfig(multipart_threshold=8 * 1024 * 1024, max_concurrency=10,
                            multipart_chunksize=8 * 1024 * 1024, use_threads=True)
    s3_client = boto3.client("s3")
    # Check if file already exists in S3
    try:
        s3_client.head_object(Bucket="ai-podcast-clipper10", Key=output_s3_key)
        print(f"[S3] File {output_s3_key} already exists in bucket. Skipping upload.")
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"[S3] File {output_s3_key} does not exist. Uploading...")
            s3_client.upload_file(
                str(subtitle_output_path),
                "ai-podcast-clipper10",
                output_s3_key,
                Config=config
            )
        else:
            raise

    # After S3 upload, clean up intermediate files unless in debug mode
    if not debug:
        for f in [clip_segment_path, audio_path, vertical_mp4_path, subtitle_output_path]:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"[CLEANUP] Removed {f}")
            except Exception as cleanup_err:
                print(f"[CLEANUP] Could not remove {f}: {cleanup_err}")
    else:
        print("[DEBUG] Skipping cleanup of intermediate files.")

def chunk_transcript_words(transcript_words, chunk_duration=600):
    """Split transcript_words (list of word dicts) into chunks of chunk_duration seconds (default 10 min)."""
    chunks = []
    current_chunk = []
    current_start = transcript_words[0]['start'] if transcript_words else 0
    for word in transcript_words:
        if not current_chunk:
            current_start = word['start']
        current_chunk.append(word)
        if word['end'] - current_start >= chunk_duration:
            chunks.append(current_chunk)
            current_chunk = []
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def select_viral_clips_with_gemini(transcript_words, gemini_model):
    """
    Use Gemini to extract viral moments from the WhisperX transcript (list of word dicts), chunked for long podcasts.
    Now works for short podcasts (5–10 min) by allowing any interesting, engaging, or highlight moments (not just Q&A/stories).
    Returns a list of dicts: [{'start': float, 'end': float, 'label': str}, ...]
    """
    import json
    all_viral_segments = []
    chunks = chunk_transcript_words(transcript_words, chunk_duration=600)  # 10 min chunks
    print(f"[DEBUG] Transcript split into {len(chunks)} chunks for Gemini processing.")
    for i, chunk in enumerate(chunks):
        transcript_str = " ".join([w['word'] for w in chunk])
        prompt = (
            "This is a podcast video transcript consisting of words, each with a start and end time. "
            "I am looking to create clips between a minimum of 10 and maximum of 60 seconds long. The clip should never exceed 60 seconds.\n"
            "Your task is to find and extract the most interesting, engaging, or highlight moments from the transcript.\n"
            "These could be stories, jokes, strong opinions, emotional moments, or question and answer exchanges.\n"
            "Each clip should be a self-contained moment that would be engaging for a short-form video audience.\n"
            "It is acceptable for the clip to include a few additional sentences before or after the main moment if it aids in context.\n"
            "Please adhere to the following rules:\n"
            "- Ensure that clips do not overlap with one another.\n"
            "- Start and end timestamps of the clips should align perfectly with the sentence boundaries in the transcript.\n"
            "- Only use the start and end timestamps provided in the input. Modifying timestamps is not allowed.\n"
            "- Format the output as a list of JSON objects, each representing a clip with 'start' and 'end' timestamps: [{\"start\": seconds, \"end\": seconds}, ...clip2, clip3]. The output should always be readable by the python json.loads function.\n"
            "- Aim to generate longer clips between 30-60 seconds if possible, but allow shorter (10+ seconds) if the moment is strong.\n"
            "Avoid including:\n"
            "- Moments of greeting, thanking, or saying goodbye.\n"
            "If there are no valid clips to extract, the output should be an empty list [], in JSON format. Also readable by json.loads() in Python.\n"
            f"The transcript is as follows:\n\n{chunk}"
        )
        response = gemini_model.generate_content(prompt)
        print(f"[DEBUG] Gemini raw response for chunk {i}:", response.text)
        cleaned_json_string = response.text.strip()
        if cleaned_json_string.startswith("```json"):
            cleaned_json_string = cleaned_json_string[len("```json"):].strip()
        if cleaned_json_string.endswith("```"):
            cleaned_json_string = cleaned_json_string[:-3].strip()
        try:
            viral_segments = json.loads(cleaned_json_string)
            print(f"[DEBUG] Parsed viral_segments for chunk {i}:", viral_segments)
            if isinstance(viral_segments, list):
                all_viral_segments.extend(viral_segments)
            else:
                print(f"[ERROR] Gemini did not return a list for chunk {i}.")
        except Exception as e:
            print(f"[ERROR] Could not parse Gemini output as JSON for chunk {i}:", e)
            print(f"[ERROR] Gemini output was for chunk {i}:", cleaned_json_string)
    print(f"[DEBUG] Total viral segments found: {len(all_viral_segments)}")
    return all_viral_segments

def whisperx_transcribe(audio_path: pathlib.Path) -> list:
    """
    Transcribe audio using WhisperX and return a list of word segments.
    """
    import whisperx
    model = whisperx.load_model("large-v2", device="cuda", compute_type="float16")
    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=16)
    # Optionally align words if you want word-level timestamps
    # alignment_model, metadata = whisperx.load_align_model(language_code="en", device="cuda")
    # result = whisperx.align(result["segments"], alignment_model, metadata, audio, device="cuda")
    segments = []
    if "word_segments" in result:
        for word_segment in result["word_segments"]:
            segments.append({
                "start": word_segment["start"],
                "end": word_segment["end"],
                "word": word_segment["word"],
            })
    return segments

def main():
    parser = argparse.ArgumentParser(description="Run the podcast viral clip pipeline locally.")
    parser.add_argument('--input', type=str, required=True, help='Path to local video file or YouTube URL')
    parser.add_argument('--use_youtube', action='store_true', help='Set if input is a YouTube URL')
    parser.add_argument('--output_dir', type=str, default='output_clips', help='Directory to save output clips')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (skip cleanup, verbose logs)')
    args = parser.parse_args()

    # Download video if YouTube URL
    if args.use_youtube:
        print(f"[INFO] Downloading YouTube video: {args.input}")
        from ytdownload import download_youtube_video
        video_path = download_youtube_video(args.input)
    else:
        video_path = args.input

    # Run the pipeline (adapted from process_video)
    print(f"[INFO] Processing video: {video_path}")
    # You may need to adapt the following to match your pipeline's function signatures
    # Example:
    # 1. Downscale video (if needed)
    # 2. Extract audio
    # 3. Transcribe with WhisperX
    # 4. Select viral clips with Gemini
    # 5. Process clips (cut, subtitle, etc.)
    # 6. Upload to S3
    # 7. Print results
    #
    # For now, call your main pipeline function here:
    # process_video_local(video_path, output_dir=args.output_dir, debug=args.debug)
    #
    # If you don't have a single function, you can inline the steps here.
    print("[INFO] Local pipeline completed.")

if __name__ == "__main__":
    main()
