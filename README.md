🎬 ClipGenius AI — Turn Podcasts Into Viral Clips Instantly

Your SAAS! project is an AI-powered podcast clip generator that automatically creates viral short-form video clips from longer podcast content. It's designed to help content creators and podcasters extract engaging moments and convert them into vertical video clips optimized for social media platforms.
Core Functionality
🎯 Main Purpose
The system takes long-form podcast videos and automatically:
Identifies viral moments using AI
Creates vertical video clips (9:16 aspect ratio for mobile)
Adds professional subtitles
Focuses on active speakers using computer vision
Uploads to cloud storage for distribution
🔧 Technical Architecture
Backend (SAAS_Backend/)
Framework: FastAPI with Modal cloud deployment
AI Models:
WhisperX for speech-to-text transcription
Google Gemini for identifying viral moments
LR-ASD (Active Speaker Detection) for tracking who's speaking
Video Processing: FFmpeg for video manipulation
Cloud Storage: AWS S3 for storing processed clips
Key Components:
Video Processing Pipeline (main.py):
Downloads/processes input videos
Extracts audio for transcription
Cuts video segments based on AI-selected moments
Creates vertical format videos
Adds subtitles with custom styling
Active Speaker Detection (LR-ASD/):
Uses computer vision to detect faces in video frames
Tracks speakers across video segments
Determines who is actively speaking
Creates focused video crops around the active speaker
AI Content Selection:
WhisperX: Transcribes audio with word-level timestamps
Google Gemini: Analyzes transcript to find engaging moments (stories, jokes, strong opinions, emotional moments)
Chunking: Handles long podcasts by processing in 10-minute segments
A. Video Processing Features
Vertical Video Creation: Converts horizontal videos to 9:16 format (1080x1920)
Smart Cropping: Automatically focuses on the active speaker
Background Blur: Applies aesthetic background blur when no speaker is detected
Professional Subtitles: Custom-styled subtitles with proper timing
Hardware Acceleration: Uses NVIDIA GPU acceleration when available
B. Dependencies (from requirements.txt)
AI/ML: torch, transformers, whisperx, google-generativeai
Video Processing: opencv-python-headless, ffmpegcv, scenedetect
Cloud: boto3, modal
Web Framework: fastapi
Audio: python_speech_features
🚀 Deployment
Uses Modal for cloud deployment with GPU support
Docker-like containerization with CUDA 12.4 support
Volume storage for model caching
S3 integration for scalable storage
C. Use Cases
This system is perfect for:
Podcast creators wanting to create TikTok/Instagram Reels
Content marketers looking to repurpose long-form content
Social media managers needing viral clip generation
Video editors wanting to automate clip creation
D. Workflow
Input: Long podcast video (local file or YouTube URL)
Processing:
Audio extraction and transcription
AI analysis for viral moments
Video segmentation and processing
Active speaker detection and cropping
Subtitle generation
Output: Multiple vertical video clips with subtitles, uploaded to S3
The project represents a sophisticated AI-powered content automation system that bridges the gap between long-form podcast content and short-form social media consumption, using cutting-edge computer vision and natural language processing technologies.
🧩 Tech Stack
 Feature        :      Details                                                                                           
 -------------------------------------------------------------------------------------------------------------------------
 Backend                 FastAPI (Python 3.10+)                                                                            
 AI Models               WhisperX (speech-to-text), Google Gemini (highlight detection), LR-ASD (active speaker detection) 
 Video Processing        FFmpeg, OpenCV                                                                                    
 Cloud                   Modal (GPU inference), AWS S3 (storage) 

 📁 Project Structure
 
ClipGeniusAI/
├── SAAS_Backend/
│   ├── main.py               # Main processing pipeline
│   ├── requirements.txt      # Dependencies
│   ├── LR-ASD/               # Active Speaker Detection
│   │   ├── ASD.py
│   │   ├── Columbia_test.py
│   │   ├── model/
│   │   └── weight/
│   ├── fonts/                # Subtitle fonts
│   ├── tests/                # Unit tests
├── SAAS_frontend/            # (Coming soon)
├── assets/                   # Screenshots, GIFs
└── .github/                  # CONTRIBUTING.md, workflows

⚙️ Configuration

 Setting                Value            
 ------------------------------------
 Resolution          1080x1920 (9:16) 
 Frame Rate          25 FPS           
 Audio Sample Rate   16kHz            
 Subtitle Font       Anton (custom)   
 Chunk Duration      10 mins          
 Clip Duration       10–60 sec        

 🔧 Installation
 1️⃣ Clone the repo
git clone https://github.com/yourusername/clipgenius-ai.git
cd clipgenius-ai/SAAS_Backend

 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
 or
venv\Scripts\activate     # Windows

 3️⃣ Install dependencies
pip install -r requirements.txt

 4️⃣ Run the pipeline
python main.py

✨ Usage Example
python main.py --input podcast.mp4 --output clips/

Input: Long podcast video file or YouTube URL
Output: Short, viral-ready vertical clips stored in AWS S3

📈 Performance :

   ⏱️ Processing: ~2–3× real-time with NVIDIA GPU

   🧠 GPU Memory: ~8GB recommended

   🎥 Output: 1080p vertical, AAC audio


🚀 Deployment

🟢 Cloud: Uses Modal for GPU workloads

🟢 Storage: AWS S3 for scalable, reliable storage

🟢 Container: Docker-like environment with CUDA 12.4 support


🤝 Contributing
🙌 We love contributions! Please read our CONTRIBUTING.md.

Quick Start:
git checkout -b feature/my-feature
# Make changes
git commit -m "Add my feature"
git push origin feature/my-feature
Then open a Pull Request!


📜 License
This project is licensed under the MIT License. See LICENSE.

🙏 Acknowledgments
 WhisperX
 LR-ASD
 Google Gemini
 Modal


📞 Contact
📧 Email: divyanshu.work914214@gmail.com
💬 Discuss: Join Discussions on Synchubb.in
🌐 Website: Coming Soon

Built with ❤️ for creators who want to go viral, faster.


















 
 


 
 





