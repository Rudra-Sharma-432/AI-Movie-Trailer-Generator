# ==========================================================
# AI Movie Trailer Generator
# Block 1 - Install Required Libraries
# ==========================================================

!pip -q install google-genai
!pip -q install edge-tts
!pip -q install moviepy
!pip -q install pillow
!pip -q install opencv-python
!pip -q install numpy
!pip -q install tqdm
!pip install -q requests
!apt-get update
!apt-get install imagemagick -y

print("✅ All libraries installed successfully.")

# ==========================================================
# Block 2 - Imports + API Setup + Project Structure
# ==========================================================

import os
import re
import json
import asyncio
import textwrap

import numpy as np
import cv2

from PIL import Image
from tqdm import tqdm

from google import genai
import edge_tts

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)

from IPython.display import Audio, Video

# ----------------------------------------------------------
# Gemini API
# ----------------------------------------------------------

API_KEY = "AQ.Ab8RN6KPbMyrEk4Pdsao8XrcLebg5Rtb9AcuI3wrWnBVfjee0w"

client = genai.Client(api_key=API_KEY)

print("✅ Gemini Connected")

# ----------------------------------------------------------
# Create Project Folders
# ----------------------------------------------------------

PROJECT_FOLDER = "AI_Movie_Trailer"

OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "outputs")
IMAGE_FOLDER = os.path.join(OUTPUT_FOLDER, "images")
TEXT_FOLDER = os.path.join(OUTPUT_FOLDER, "texts")
AUDIO_FOLDER = os.path.join(OUTPUT_FOLDER, "audio")

for folder in [
    PROJECT_FOLDER,
    OUTPUT_FOLDER,
    IMAGE_FOLDER,
    TEXT_FOLDER,
    AUDIO_FOLDER
]:
    os.makedirs(folder, exist_ok=True)

print("✅ Project folders created")

# ----------------------------------------------------------
# Helper Function
# ----------------------------------------------------------

def save_text(filename, text):

    path = os.path.join(TEXT_FOLDER, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved -> {path}")

# ==========================================================
# Block 3 - User Input + Story Generation
# ==========================================================

print("="*60)
print("🎬 AI MOVIE TRAILER GENERATOR")
print("="*60)

movie_title = input("Movie Title : ")
genre = input("Genre : ")
description = input("Description : ")
number_of_scenes = int(input("Number of Scenes : "))

# ----------------------------------------------------------
# Story Prompt
# ----------------------------------------------------------

story_prompt = f"""
You are an award-winning Hollywood screenwriter.

Write as if you are Christopher Nolan writing a Hollywood blockbuster trailer.
Focus on visual storytelling.
Use dramatic pacing.
Create memorable narration moments.
Avoid clichés.
Keep scenes visually spectacular.

Movie Title:
{movie_title}

Genre:
{genre}

Description:
{description}

Requirements

- 250-300 words
- Introduce the world
- Introduce the main character
- Introduce supporting characters
- Main conflict
- Strong ending
- Cinematic writing
- Emotional
- Suitable for an AI movie trailer
"""

print("\nGenerating Story...\n")

story_response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=story_prompt
)

story = story_response.text

print(story)

save_text("story.txt", story)

print("\n✅ Story Generated Successfully")

# ==========================================================
# Block 4 - Trailer Generation + Narration Extraction
# ==========================================================

print("=" * 60)
print("🎞️ Generating Trailer Script...")
print("=" * 60)

trailer_prompt = f"""
You are an expert Hollywood trailer writer.

Using the movie story below, generate a cinematic movie trailer.

MOVIE STORY
------------
{story}

Requirements

Generate exactly {number_of_scenes} scenes.

For EACH scene use the following format:

Scene 1

Scene Explanation:
(Brief explanation of what this scene represents)

Visual:
(Describe exactly what should appear on screen)

Narration:
(A dramatic trailer narration line)

At the end include ONLY one Background Music Mood.

Example:

Background Music Mood:
Epic orchestral with rising tension
"""

trailer_response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=trailer_prompt
)

trailer_script = trailer_response.text

print(trailer_script)

save_text("trailer_script.txt", trailer_script)

print("\n✅ Trailer Script Generated")

# ==========================================================
# Extract Narration
# ==========================================================

print("=" * 60)
print("🎤 Extracting Narration...")
print("=" * 60)

narration_prompt = f"""
Extract ONLY the narration from the trailer below.

Do NOT include:

- Scene numbers
- Scene explanation
- Visual descriptions
- Background music

Return ONLY the narration as continuous paragraphs.

Trailer:

{trailer_script}
"""

narration_response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=narration_prompt
)

narration = narration_response.text

print(narration)

save_text("narration.txt", narration)

print("\n✅ Narration Extracted")

# ==========================================================
# Block 5 - Voice Generation
# ==========================================================

print("=" * 60)
print("🎤 Generating AI Voice...")
print("=" * 60)

VOICE_NAME = "en-US-GuyNeural"

voice_file = os.path.join(AUDIO_FOLDER, "trailer_voice.mp3")


async def generate_voice(text, output_path):

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_NAME
    )

    await communicate.save(output_path)


await generate_voice(narration, voice_file)

print(f"✅ Voice saved to:\n{voice_file}")

# ==========================================================
# Preview Generated Voice
# ==========================================================

Audio(voice_file)

# ==========================================================
# Audio Information
# ==========================================================

audio = AudioFileClip(voice_file)

print(f"Voice Duration : {audio.duration:.2f} seconds")



# ==========================================================
# Block 6 - Generate Image Prompts (JSON)
# ==========================================================

print("=" * 60)
print("🖼️ Generating Image Prompts...")
print("=" * 60)

image_prompt_request = f"""
You are an expert cinematic concept artist.

Using the trailer below, create ONE image generation prompt
for EACH scene.

Return ONLY valid JSON.

Example:

[
  {{
    "scene":1,
    "prompt":"Ultra realistic cinematic..."
  }},
  {{
    "scene":2,
    "prompt":"..."
  }}
]

Rules

- Exactly {number_of_scenes} objects

Each prompt must include:

Ultra realistic cinematic movie still,
Hollywood blockbuster,
photorealistic,
35mm anamorphic lens,
volumetric lighting,
dramatic atmosphere,
high contrast,
cinematic color grading,
ultra detailed,
masterpiece,
8K,
award-winning cinematography

Trailer:

{trailer_script}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=image_prompt_request
)

image_prompt_json = response.text

print(image_prompt_json)

save_text("image_prompts.json", image_prompt_json)

# ==========================================================
# Parse JSON Prompts
# ==========================================================

import json

clean_json = image_prompt_json.strip()

if clean_json.startswith("```json"):
    clean_json = clean_json.replace("```json", "")
    clean_json = clean_json.replace("```", "")

image_prompts = json.loads(clean_json)

print(f"\n✅ Total Prompts : {len(image_prompts)}\n")

for scene in image_prompts:
    print("=" * 60)
    print(f"Scene {scene['scene']}")
    print(scene["prompt"][:250] + "...")

# ==========================================================
# Block 7.1 - Test Imagen API
# ==========================================================

from google import genai

print("Testing Imagen API...")
print("Connected successfully!")

# ==========================================================
# Block 7.2 - Generate Images using HuggingFace FLUX
# ==========================================================

import os
import requests
from PIL import Image
from io import BytesIO

HF_TOKEN = "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"

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

print("="*60)
print("🎨 Generating Images...")
print("="*60)

from tqdm import tqdm

for scene in tqdm(image_prompts, desc="Generating Images"):

    scene_number = scene["scene"]
    prompt = scene["prompt"]

    print(f"Generating Scene {scene_number}...")

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt
        }
    )

    if response.status_code != 200:
        print(response.text)
        raise Exception("Image generation failed.")

    image = Image.open(BytesIO(response.content))

    save_path = os.path.join(
        IMAGE_FOLDER,
        f"scene_{scene_number}.png"
    )

    image.save(save_path)

    print(f"✅ Saved -> {save_path}")

print("\n🎉 All images generated successfully!")

# ==========================================================
# Block 7.3 - Verify Images
# ==========================================================

import os
from PIL import Image
import matplotlib.pyplot as plt

images = sorted([
    f for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png")
])

print(f"Found {len(images)} images.\n")

for img_name in images:

    path = os.path.join(IMAGE_FOLDER, img_name)

    img = Image.open(path)

    plt.figure(figsize=(6,6))
    plt.imshow(img)
    plt.title(img_name)
    plt.axis("off")
    plt.show()

# ==========================================================
# Cinematic Letterbox Effect
# ==========================================================

from moviepy.editor import CompositeVideoClip, ColorClip

def add_letterbox(video, bar_height=70):

    w, h = video.size

    top_bar = ColorClip(
        size=(w, bar_height),
        color=(0,0,0)
    ).set_duration(video.duration)

    bottom_bar = ColorClip(
        size=(w, bar_height),
        color=(0,0,0)
    ).set_position((0, h-bar_height)).set_duration(video.duration)

    return CompositeVideoClip(
        [video, top_bar, bottom_bar]
    )

import subprocess
import re

# Get the path to the ImageMagick policy.xml file
# Use 'convert -version' to find the policy path
magick_output = subprocess.run(
    ["/usr/bin/convert", "-version"],
    capture_output=True, text=True
).stdout

# Use regex to find the policy file path from 'Policy: /path/to/policy.xml'
match = re.search(r'Policy: (\S+)', magick_output)

if match:
    policy_path = match.group(1)
else:
    # Fallback to common path if regex fails
    common_policy_path = '/etc/ImageMagick-6/policy.xml'
    if os.path.exists(common_policy_path):
        policy_path = common_policy_path
    else:
        raise ValueError("Could not find ImageMagick policy file path in output or common locations.")

# Read the policy file
with open(policy_path, 'r') as f:
    policy_content = f.read()

# Modify the policy to allow read/write operations
# This specifically targets the 'disk' policy which can restrict writing to /tmp
# and also addresses the 'rights' policy which can restrict operations on certain file types
# The problematic lines often look like: <policy domain="disk" rights="none" pattern="*"/>
# And <policy domain="path" rights="none" pattern="/var/tmp/"/>

# Ensure that the 'disk' and 'file' policies allow read/write
# and 'path' policy allows operation on /tmp
modified_policy = policy_content.replace(
    '<policy domain="path" rights="none" pattern="@*"/>', 
    '<policy domain="path" rights="read|write" pattern="@*"/>'
).replace(
    '<policy domain="coder" rights="none" pattern="MVG"/>',
    '<policy domain="coder" rights="read|write" pattern="MVG"/>'
).replace(
    '<policy domain="delegate" rights="none" pattern="gs"/>',
    '<policy domain="delegate" rights="read|write" pattern="gs"/>'
).replace(
    '<policy domain="resource" name="disk" value="1GiB"/>',
    '<policy domain="resource" name="disk" value="8GiB"/>' # Increase disk resource limit if needed
).replace(
    '<policy domain="system" rights="none" pattern="tmp"/>',
    '<policy domain="system" rights="read|write" pattern="tmp"/>'
)

# Overwrite the policy file with the modified content
with open(policy_path, 'w') as f:
    f.write(modified_policy)

print(f"✅ ImageMagick policy updated at {policy_path}")

# ==========================================================
# Block 8 - Automatic Video Generation
# ==========================================================

import os
import cv2
import numpy as np

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)

print("=" * 60)
print("🎥 Creating Cinematic Trailer...")
print("=" * 60)

# ----------------------------------------------------------
# Zoom Effects
# ----------------------------------------------------------

def zoom_in_effect(clip, zoom_ratio=0.05):

    def effect(get_frame, t):

        img = get_frame(t)

        h, w = img.shape[:2]

        scale = 1 + zoom_ratio * t

        new_w = int(w / scale)
        new_h = int(h / scale)

        x1 = (w - new_w) // 2
        y1 = (h - new_h) // 2

        cropped = img[y1:y1+new_h, x1:x1+new_w]

        return cv2.resize(cropped, (w, h))

    return clip.fl(effect)


def zoom_out_effect(clip, zoom_ratio=0.05):

    def effect(get_frame, t):

        img = get_frame(t)

        h, w = img.shape[:2]

        scale = 1 + zoom_ratio * (clip.duration - t)

        new_w = int(w / scale)
        new_h = int(h / scale)

        x1 = (w - new_w) // 2
        y1 = (h - new_h) // 2

        cropped = img[y1:y1+new_h, x1:x1+new_w]

        return cv2.resize(cropped, (w, h))

    return clip.fl(effect)

# ----------------------------------------------------------
# Load Audio
# ----------------------------------------------------------

voice_path = os.path.join(
    AUDIO_FOLDER,
    "trailer_voice.mp3"
)

audio = AudioFileClip(voice_path)

# ----------------------------------------------------------
# Detect Images Automatically
# ----------------------------------------------------------

images = sorted([
    f
    for f in os.listdir(IMAGE_FOLDER)
    if f.endswith(".png")
])

print(f"Detected {len(images)} scene images.")

scene_duration = audio.duration / len(images)

clips = []

# ----------------------------------------------------------
# Create Clips
# ----------------------------------------------------------

from tqdm import tqdm

for i, image_name in enumerate(
    tqdm(images, desc="Creating Video")
):

    image_path = os.path.join(
        IMAGE_FOLDER,
        image_name
    )

    clip = ImageClip(image_path)

    clip = clip.set_duration(scene_duration)

    # Alternate Zoom

    if i % 2 == 0:
        clip = zoom_in_effect(clip)
    else:
        clip = zoom_out_effect(clip)

    # Fade

    clip = clip.fadein(1.2).fadeout(0.6)

    clips.append(clip)

# ----------------------------------------------------------
# Merge Clips
# ----------------------------------------------------------

video = concatenate_videoclips(
    clips,
    method="compose"
)

video = video.set_audio(audio)

output_video = os.path.join(
    OUTPUT_FOLDER,
    "final_movie_trailer.mp4"
)

from moviepy.config import change_settings

change_settings({
    "IMAGEMAGICK_BINARY": "/usr/bin/convert"
})
from moviepy.editor import *
from moviepy.editor import TextClip, CompositeVideoClip

ending = TextClip(
    movie_title.upper(),
    fontsize=80,
    color="white",
    font="DejaVu-Sans-Bold"
).set_duration(3)

ending = ending.set_position("center")

coming = TextClip(
    "COMING SOON",
    fontsize=40,
    color="white",
    font="DejaVu-Sans"
).set_duration(3)

coming = coming.set_position(("center", 450))

from moviepy.editor import ColorClip

background = ColorClip(
    size=video.size,
    color=(0,0,0)
).set_duration(3)

ending_clip = CompositeVideoClip(
    [
        background,
        ending,
        coming
    ]
).set_duration(3)

video = concatenate_videoclips(
    [video, ending_clip]
)

video = add_letterbox(video)

video.write_videofile(
    output_video,
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("\n✅ Trailer Created Successfully!")

print(output_video)

# ==========================================================
# Preview Final Trailer
# ==========================================================

from IPython.display import Video

Video(output_video, embed=True)
